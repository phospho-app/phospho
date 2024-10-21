import time
from collections import defaultdict
import traceback
from typing import Dict, List, Optional, Tuple, cast

from extractor.utils import generate_uuid
from loguru import logger

from extractor.db.models import (
    Event,
    EventDefinition,
    LlmCall,
    Recipe,
    Task,
)
from extractor.db.mongo import get_mongo_db
from extractor.services.data import fetch_previous_tasks
from extractor.services.projects import get_project_by_id
from extractor.services.sentiment_analysis import call_sentiment_and_language_api
from extractor.services.webhook import trigger_webhook
from extractor.utils import get_most_common
from phospho import lab
from phospho.models import (
    JobResult,
    ResultType,
    SentimentObject,
    SessionStats,
    Project,
    PipelineResults,
    Message,
)
import asyncio

PHOSPHO_EVENT_MODEL_NAMES = ["phospho-6", "owner", "phospho-4"]
PHOSPHO_EVAL_MODEL_NAMES = ["phospho", "phospho-4"]


class EventConfig(lab.JobConfig):
    event_name: str
    event_description: str


class MainPipeline:
    project_id: str
    project: Optional[Project] = None
    messages: List[lab.Message]

    def __init__(self, project_id: str, org_id: str):
        self.project_id = project_id
        self.org_id = org_id
        self.project = None
        self.messages = []

    async def set_input(
        self,
        task: Optional[Task] = None,
        tasks: Optional[List[Task]] = None,
        tasks_ids: Optional[List[str]] = None,
        messages: Optional[List[lab.Message]] = None,
    ) -> None:
        """
        Set the input for the pipeline.
        """

        self.project = await get_project_by_id(self.project_id)
        cast(Project, self.project)
        mongo_db = await get_mongo_db()
        llm_based_events = []
        for event_name, event in self.project.settings.events.items():
            if event.detection_engine == "llm_detection":
                llm_based_events.append(event_name)

        # Matches at most one successful example per event_name
        successful_events = (
            await mongo_db["events"]
            .aggregate(
                [
                    {
                        "$match": {
                            "project_id": self.project_id,
                            "source": {"$in": PHOSPHO_EVENT_MODEL_NAMES},
                            "confirmed": True,
                            "removed": False,
                            "event_name": {
                                "$in": llm_based_events
                            },  # filter by event names in project.settings.event
                        }
                    },
                    {
                        "$facet": {
                            "event_names": [{"$group": {"_id": "$event_name"}}],
                            "events": [
                                {"$sort": {"created_at": -1}},
                                {
                                    "$group": {
                                        "_id": "$event_name",
                                        "first_event": {"$first": "$$ROOT"},
                                    }
                                },
                                {"$replaceRoot": {"newRoot": "$first_event"}},
                                {
                                    "$lookup": {
                                        "from": "tasks",
                                        "localField": "task_id",
                                        "foreignField": "id",
                                        "as": "task",
                                    }
                                },
                                {"$unwind": "$task"},
                                {
                                    "$addFields": {
                                        "event_name": "$event_name",
                                        "output": "$task.output",
                                        "input": "$task.input",
                                    }
                                },
                                {
                                    "$project": {
                                        "input": 1,
                                        "output": 1,
                                        "event_name": 1,
                                    }
                                },
                            ],
                        }
                    },
                    {
                        "$project": {
                            "events": {
                                "$setDifference": [
                                    "$events",
                                    {
                                        "$map": {
                                            "input": "$event_names",
                                            "as": "event_name",
                                            "in": {
                                                "$filter": {
                                                    "input": "$events",
                                                    "as": "event",
                                                    "cond": {
                                                        "$eq": [
                                                            "$$event.event_name",
                                                            "$$event_name._id",
                                                        ]
                                                    },
                                                }
                                            },
                                        }
                                    },
                                ]
                            }
                        }
                    },
                    {"$unwind": "$events"},
                    {"$replaceRoot": {"newRoot": "$events"}},
                ]
            )
            .to_list(length=None)
        )

        # Matches at most one unsuccessful example per event_name
        unsuccessful_events = (
            await mongo_db["events"]
            .aggregate(
                [
                    {
                        "$match": {
                            "project_id": self.project_id,
                            "removed": True,
                            "confirmed": False,
                            "source": {"$in": PHOSPHO_EVENT_MODEL_NAMES},
                            "removal_reason": {"$regex": "removed_by_user"},
                            "event_name": {"$in": llm_based_events},
                        }
                    },
                    {
                        "$facet": {
                            "event_names": [{"$group": {"_id": "$event_name"}}],
                            "events": [
                                {"$sort": {"created_at": -1}},
                                {
                                    "$group": {
                                        "_id": "$event_name",
                                        "first_event": {"$first": "$$ROOT"},
                                    }
                                },
                                {"$replaceRoot": {"newRoot": "$first_event"}},
                                {
                                    "$lookup": {
                                        "from": "tasks",
                                        "localField": "task_id",
                                        "foreignField": "id",
                                        "as": "task",
                                    }
                                },
                                {"$unwind": "$task"},
                                {
                                    "$addFields": {
                                        "event_name": "$event_name",
                                        "output": "$task.output",
                                        "input": "$task.input",
                                    }
                                },
                                {
                                    "$project": {
                                        "input": 1,
                                        "output": 1,
                                        "event_name": 1,
                                    }
                                },
                            ],
                        }
                    },
                    {
                        "$project": {
                            "events": {
                                "$setDifference": [
                                    "$events",
                                    {
                                        "$map": {
                                            "input": "$event_names",
                                            "as": "event_name",
                                            "in": {
                                                "$filter": {
                                                    "input": "$events",
                                                    "as": "event",
                                                    "cond": {
                                                        "$eq": [
                                                            "$$event.event_name",
                                                            "$$event_name._id",
                                                        ]
                                                    },
                                                }
                                            },
                                        }
                                    },
                                ]
                            }
                        }
                    },
                    {"$unwind": "$events"},
                    {"$replaceRoot": {"newRoot": "$events"}},
                ]
            )
            .to_list(length=None)
        )

        metadata = {
            "successful_events": successful_events,
            "unsuccessful_events": unsuccessful_events,
        }

        self.messages = []
        if task:
            # Get the data of all the tasks before task[task_id]
            previous_tasks = await fetch_previous_tasks(task.id)
            if len(previous_tasks) > 1:
                task_context = previous_tasks[:-1]
            else:
                task_context = []
            self.messages.append(
                lab.Message.from_task(
                    task=task, metadata=metadata, previous_tasks=task_context
                )
            )
        if tasks_ids:
            # Fetch the tasks from the database
            raw_tasks_from_ids = (
                await mongo_db["tasks"]
                .find({"id": {"$in": tasks_ids}, "project_id": self.project_id})
                .to_list(length=None)
            )
            valid_tasks_from_ids = [
                Task.model_validate(task) for task in raw_tasks_from_ids
            ]
            if tasks is None:
                tasks = []
            tasks.extend(valid_tasks_from_ids)
        if tasks:
            for task in tasks:
                # Get the data of all the tasks before task[task_id]
                previous_tasks = await fetch_previous_tasks(task.id)
                if len(previous_tasks) > 1:
                    task_context = previous_tasks[:-1]
                else:
                    task_context = []
                self.messages.append(
                    lab.Message.from_task(
                        task=task, metadata=metadata, previous_tasks=task_context
                    )
                )
        if messages:
            last_message = messages[-1]
            if len(messages) > 1:
                context = messages[:-1]
            else:
                context = []
            self.messages.append(
                lab.Message(
                    id=last_message.id,
                    created_at=last_message.created_at,
                    role=last_message.role,
                    content=last_message.content,
                    previous_messages=context,
                    metadata=metadata,
                )
            )

    async def run_events(
        self, recipe: Optional[Recipe] = None
    ) -> Dict[str, List[Event]]:
        """
        Run the main event detection pipeline on the messages
        """
        if self.project is None:
            self.project = await get_project_by_id(self.project_id)

        if not self.project.settings.run_event_detection:
            logger.info(
                f"run_event_detection is disabled for project {self.project_id}"
            )
            return {}

        # If the recipe is provided, we use it to run the workload
        # Otherwise, we use the project settings
        if recipe:
            self.workload = lab.Workload.from_phospho_recipe(recipe)
            self.workload.org_id = recipe.org_id
            self.workload.project_id = recipe.project_id
        else:
            self.workload = lab.Workload.from_phospho_project_config(self.project)
        logger.info(
            f"Running event detection pipeline for project {self.project_id} on {len(self.messages)} messages with {len(self.workload.jobs)} jobs"
        )
        # Run
        await self.workload.async_run(
            messages=self.messages, executor_type="parallel_jobs"
        )

        if self.workload.results is None or self.workload.jobs is None:
            logger.error("Worlkload.results is None")
            return {}

        events_per_task_to_return: Dict[str, List[Event]] = defaultdict(list)
        events_to_push_to_db: List[dict] = []
        job_results_to_push_to_db: List[dict] = []
        llm_calls_to_push_to_db: List[dict] = []

        # Iter over the results
        for message in self.messages:
            results = self.workload.results.get(message.id, {})
            for event_name, result in results.items():
                # event_name is the primary key of the table
                # Get back the event definition from the job metadata
                event_definition = EventDefinition.model_validate(
                    self.workload.jobs[result.job_id].metadata
                )
                task = message.metadata.get("task", None)
                try:
                    valid_task = Task.model_validate(task)
                except Exception as e:
                    logger.error(f"Error validating task: {e}")
                    continue
                task_id = valid_task.id
                session_id = valid_task.session_id

                # Store the LLM call in the database
                llm_call = result.metadata.get("llm_call", None)
                if llm_call is not None:
                    llm_call_obj = LlmCall(
                        **llm_call,
                        org_id=self.org_id,
                        project_id=self.project_id,
                        task_id=task_id,
                        recipe_id=result.job_metadata.get("recipe_id"),
                    )
                    llm_calls_to_push_to_db.append(llm_call_obj.model_dump())
                else:
                    logger.warning(f"No LLM call detected for event {event_name}")

                detected_event_data = Event(
                    event_name=event_name,
                    # Events detected at the session scope are not linked to a task
                    task_id=task_id,
                    session_id=session_id,
                    project_id=self.project_id,
                    source=result.metadata.get("evaluation_source", "phospho-unknown"),
                    webhook=event_definition.webhook,
                    org_id=self.org_id,
                    event_definition=event_definition,
                    task=valid_task,
                    score_range=result.metadata.get("score_range", None),
                )

                if result.value:
                    logger.info(f"Event {event_name} detected for task {task_id}")
                    if (
                        event_definition.webhook is not None
                        and event_definition.webhook != ""
                    ):
                        logger.info(f"Webhook url: {event_definition.webhook}")
                        await trigger_webhook(
                            url=event_definition.webhook,
                            json=detected_event_data.model_dump(),
                            headers=event_definition.webhook_headers,
                        )
                    events_to_push_to_db.append(detected_event_data.model_dump())

                events_per_task_to_return[task_id].append(detected_event_data)
                # Save the prediction
                result.task_id = task_id
                if result.job_metadata.get("recipe_id") is None:
                    logger.error(f"No recipe_id found for event {event_name}.")
                job_results_to_push_to_db.append(result.model_dump())

        # Save the detected events and jobs results in the database
        mongo_db = await get_mongo_db()
        if len(events_to_push_to_db) > 0:
            try:
                await mongo_db["events"].insert_many(events_to_push_to_db)
            except Exception as e:
                logger.error(f"Error saving detected events to the database: {e}")
        if len(llm_calls_to_push_to_db) > 0:
            try:
                await mongo_db["llm_calls"].insert_many(llm_calls_to_push_to_db)
            except Exception as e:
                logger.error(f"Error saving LLM calls to the database: {e}")
        if len(job_results_to_push_to_db) > 0:
            try:
                await mongo_db["job_results"].insert_many(job_results_to_push_to_db)
            except Exception as e:
                logger.error(f"Error saving job results to the database: {e}")

        return events_per_task_to_return

    async def update_version_id(self) -> None:
        if self.project is None:
            self.project = await get_project_by_id(self.project_id)

        mongo_db = await get_mongo_db()
        tasks_ids = [
            Task.model_validate(message.metadata.get("task", None)).id
            for message in self.messages
        ]

        # Update the task metadata with the AB version id from the platform settings
        if (
            self.project.settings is not None
            and self.project.settings.ab_version_id is not None
        ):
            mongo_db["tasks"].update_many(
                {
                    "id": {"$in": tasks_ids},
                    "$or": [
                        {
                            "metadata.version_id": {"$exists": False}
                        },  # We don't want to overwrite the version_id if it already exists
                        {"metadata.version_id": None},
                    ],
                },
                {
                    "$set": {
                        "metadata.version_id": self.project.settings.ab_version_id,
                    }
                },
            )

    async def compute_session_info_pipeline(self) -> Dict[str, SessionStats]:
        """
        Compute session information from its tasks
        - Average sentiment score
        - Average sentiment magnitude
        - Most common sentiment label
        - Most common language
        - Most common flag
        - Last message timestamp
        """
        outputs: Dict[str, SessionStats] = {}

        session_ids: List[str] = []
        for message in self.messages:
            task = Task.model_validate(message.metadata.get("task", None))
            if task.session_id is not None:
                session_ids.append(task.session_id)
        unique_session_ids = list(set(session_ids))

        for session_id in unique_session_ids:
            logger.debug(f"Compute session info for session {session_id}")
            mongo_db = await get_mongo_db()
            tasks = (
                await mongo_db["tasks"]
                .find(
                    {
                        "project_id": self.project_id,
                        "session_id": session_id,
                    },
                )
                .to_list(length=None)
            )

            sentiment_score: list = []
            sentiment_magnitude: list = []
            preview = ""
            last_message_ts = None

            valid_tasks = [Task.model_validate(task) for task in tasks]
            for valid_task in valid_tasks:
                if valid_task.sentiment is not None:
                    if valid_task.sentiment.score is not None:
                        sentiment_score.append(valid_task.sentiment.score)
                    if valid_task.sentiment.magnitude is not None:
                        sentiment_magnitude.append(valid_task.sentiment.magnitude)
                preview += valid_task.preview() + "\n"
                if last_message_ts is None or valid_task.created_at > last_message_ts:
                    last_message_ts = valid_task.created_at

            if len(valid_tasks) > 0:
                avg_sentiment_score = None
                if len(sentiment_score) > 0:
                    avg_sentiment_score = sum(sentiment_score) / len(sentiment_score)
                avg_magnitude_score = None
                if len(sentiment_magnitude) > 0:
                    avg_magnitude_score = sum(sentiment_magnitude) / len(
                        sentiment_magnitude
                    )

                session_task_info = SessionStats(
                    avg_sentiment_score=avg_sentiment_score,
                    avg_magnitude_score=avg_magnitude_score,
                    most_common_sentiment_label=get_most_common(
                        [
                            task.sentiment.label
                            for task in valid_tasks
                            if task.sentiment is not None
                        ]
                    ),
                    most_common_language=get_most_common(
                        [
                            task.language
                            for task in valid_tasks
                            if task.language is not None
                        ]
                    ),
                    most_common_flag=get_most_common(
                        [task.flag for task in valid_tasks if task.flag is not None]
                    ),
                    human_eval=get_most_common(
                        [
                            task.human_eval.flag
                            for task in valid_tasks
                            if task.human_eval
                        ]
                    ),
                )

                mongo_db["sessions"].update_one(
                    {"id": session_id},
                    {
                        "$set": {
                            "stats": session_task_info.model_dump(),
                            "preview": preview if preview else None,
                            "last_message_ts": last_message_ts,
                        }
                    },
                )

            outputs[session_id] = session_task_info

        return outputs

    async def run_sentiment_and_language(
        self,
    ) -> Tuple[Dict[str, Optional[SentimentObject]], Dict[str, Optional[str]]]:
        """
        Run the sentiment analysis on the input of a task
        """
        mongo_db = await get_mongo_db()

        if not self.project:
            self.project = await get_project_by_id(self.project_id)

        if (
            self.project.settings is not None
            and self.project.settings.run_sentiment is not None
            and self.project.settings.run_language is not None
            and not self.project.settings.run_sentiment
            and not self.project.settings.run_language
        ):
            logger.info(f"Sentiment analysis is disabled for project {self.project_id}")
            return {}, {}

        # Default values
        score_threshold = 0.3
        magnitude_threshold = 0.6
        # Try to replace with project settings
        if self.project.settings.sentiment_threshold is not None:
            if self.project.settings.sentiment_threshold.score is not None:
                score_threshold = self.project.settings.sentiment_threshold.score
            else:
                mongo_db["projects"].update_one(
                    {"id": self.project_id},
                    {
                        "$set": {
                            "settings.sentiment_threshold.score": 0.3,
                        }
                    },
                )

            if self.project.settings.sentiment_threshold.magnitude is not None:
                magnitude_threshold = (
                    self.project.settings.sentiment_threshold.magnitude
                )
            else:
                mongo_db["projects"].update_one(
                    {"id": self.project_id},
                    {
                        "$set": {
                            "settings.sentiment_threshold.magnitude": 0.6,
                        }
                    },
                )
        else:
            mongo_db["projects"].update_one(
                {"id": self.project_id},
                {
                    "$set": {
                        "settings.sentiment_threshold": {
                            "score": 0.3,
                            "magnitude": 0.6,
                        }
                    }
                },
            )

        logger.info(
            f"Running sentiment analysis pipeline for project {self.project_id} for {len(self.messages)} messages"
        )

        async def process_message(
            message: Message,
        ) -> Tuple[str, Optional[SentimentObject], Optional[str]]:
            task = Task.model_validate(message.metadata.get("task", None))
            sentiment_object: Optional[SentimentObject] = None
            sentiment_object, language = await call_sentiment_and_language_api(
                task.input, score_threshold, magnitude_threshold
            )
            if not self.project or not self.project.settings:
                language = None
                sentiment_object = None
            elif not self.project.settings.run_language:
                language = None
            elif not self.project.settings.run_sentiment:
                sentiment_object = None

            # Update the task item
            mongo_db["tasks"].update_one(
                {
                    "id": task.id,
                    "project_id": task.project_id,
                },
                {
                    "$set": {
                        "sentiment": sentiment_object.model_dump()
                        if sentiment_object
                        else None,
                        "language": language,
                        "metadata.sentiment_score": sentiment_object.score
                        if sentiment_object
                        else None,
                        "metadata.sentiment_magnitude": sentiment_object.magnitude
                        if sentiment_object
                        else None,
                        "metadata.sentiment_label": sentiment_object.label
                        if sentiment_object
                        else None,
                        "metadata.language": language,
                    }
                },
            )

            if sentiment_object:
                jobresult = JobResult(
                    org_id=task.org_id,
                    project_id=task.project_id,
                    job_id="sentiment_analysis",
                    value=sentiment_object.model_dump(),
                    result_type=ResultType.dict,
                    metadata={
                        "input": task.input,
                    },
                )
                mongo_db["job_results"].insert_one(jobresult.model_dump())
                logger.info(
                    f"Sentiment analysis for task {task.id} : {sentiment_object}"
                )

            return task.id, sentiment_object, language

        tasks = [process_message(message) for message in self.messages]
        results = await asyncio.gather(*tasks)

        results_sentiment: Dict[str, Optional[SentimentObject]] = {}
        results_language: Dict[str, Optional[str]] = {}
        for task_id, sentiment, language in results:
            results_sentiment[task_id] = sentiment
            results_language[task_id] = language

        return results_sentiment, results_language

    async def recipe_pipeline(
        self,
        recipe: Recipe,
        tasks: Optional[List[Task]] = None,
        tasks_ids: Optional[List[str]] = None,
    ):
        """
        Run a recipe on a task
        """
        logger.info(f"RECIPE PIPELINE: Running recipe {recipe.recipe_type} {recipe.id}")
        await self.set_input(tasks=tasks, tasks_ids=tasks_ids)

        if recipe.recipe_type == "event_detection":
            await self.run_events(recipe=recipe)
            await self.compute_session_info_pipeline()
        elif recipe.recipe_type == "sentiment_language":
            await self.run_sentiment_and_language()
            await self.compute_session_info_pipeline()
        else:
            raise NotImplementedError(
                f"Recipe type {recipe.recipe_type} not implemented"
            )

    async def run(self) -> PipelineResults:
        """
        Run the main pipeline
        """
        # Run the event detection pipeline
        try:
            events = await self.run_events()
        except Exception as e:
            error_id = generate_uuid()
            error_message = f"Caught error while running event detection (error_id: {error_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)
            traceback.print_exc()
            events = {}
        # Run sentiment analysis on the user input
        try:
            sentiments, languages = await self.run_sentiment_and_language()
        except Exception as e:
            error_id = generate_uuid()
            error_message = f"Caught error while running sentiment analysis (error_id: {error_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)
            traceback.print_exc()
            sentiments = {}
            languages = {}

        # Update metadata
        try:
            await self.compute_session_info_pipeline()
        except Exception as e:
            logger.error(f"Error computing session info: {e}")
        try:
            await self.update_version_id()
        except Exception as e:
            logger.error(f"Error updating the version id: {e}")

        logger.info("Main pipeline completed")
        return PipelineResults(
            events=events,
            language=languages,
            sentiment=sentiments,
        )

    async def task_main_pipeline(self, task: Task) -> PipelineResults:
        """
        Main pipeline to run on a task.
        - Event detection
        - Evaluate task success/failure
        - Language detection
        - Sentiment analysis
        """
        self.start_time = time.time()
        logger.info(f"Starting main pipeline for task {task.id}")
        # Set the input for the pipeline
        await self.set_input(task=task)
        pipeline_results = await self.run()
        logger.info(
            f"Main pipeline completed in {time.time() - self.start_time:.2f} seconds for task {task.id}"
        )

        return pipeline_results

    async def messages_main_pipeline(self, messages: List[lab.Message]) -> dict:
        """
        Main pipeline to run on a list of messages.
        We expect the messages to be in chronological order.
        Only the last message will be used for the event detection.
        The previous messages will be used as context.

        - Event detection
        """
        await self.set_input(messages=messages)
        pipeline_results = await self.run()
        result = pipeline_results.model_dump()
        result["action"] = "messages_main_pipeline"
        return result

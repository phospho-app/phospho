from collections import defaultdict
from typing import Literal, cast

import pydantic
from fastapi import HTTPException
from loguru import logger
from phospho.models import FlattenedTask, HumanEval, ProjectDataFilters, ScoreRange
from phospho.utils import filter_nonjsonable_keys
from phospho_backend.api.platform.models.explore import Pagination, Sorting
from phospho_backend.db.models import Eval, Event, EventDefinition, Task
from phospho_backend.db.mongo import get_mongo_db
from phospho_backend.services.mongo.query_builder import QueryBuilder
from phospho_backend.utils import generate_uuid
from pymongo import InsertOne, UpdateOne


async def create_task(
    project_id: str,
    org_id: str,
    input: str,
    task_id: str | None = None,
    output: str | None = None,
    additional_input: dict | None = None,
    data: dict | None = None,
    session_id: str | None = None,
    flag: str | None = None,
) -> Task:
    mongo_db = await get_mongo_db()
    if task_id is None:
        task_id = generate_uuid()
    task_data = Task(
        id=task_id,
        input=input,
        project_id=project_id,
        org_id=org_id,
        session_id=session_id,
        output=output,
        additional_input=additional_input,
        data=data,
        flag=flag,
    )
    # Filter non-jsonable values
    if task_data.metadata is not None:
        task_data.metadata = filter_nonjsonable_keys(task_data.metadata)

    # Create a new task
    doc_creation = await mongo_db["tasks"].insert_one(task_data.model_dump())
    if not doc_creation:
        raise Exception("Failed to insert the task in database")
    return task_data


async def get_task_by_id(task_id: str) -> Task:
    mongo_db = await get_mongo_db()
    query_builder = QueryBuilder(
        project_id=None,
        fetch_objects="tasks_with_events",
        filters=ProjectDataFilters(tasks_ids=[task_id]),
    )
    pipeline = await query_builder.build()
    fetched_tasks = await mongo_db["tasks"].aggregate(pipeline).to_list(length=1)
    if fetched_tasks is None or len(fetched_tasks) == 0:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    task = fetched_tasks[0]

    # Account for schema discrepancies
    if "id" not in task.keys():
        task["id"] = task_id

    if task["flag"] == "undefined":
        task["flag"] = None

    try:
        task = Task.model_validate(task, strict=True)
    except pydantic.ValidationError as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate task: {e}")
    return task


async def human_eval_task(
    task_model: Task,
    human_eval: str,
    source: str | None = None,
    notes: str | None = None,
) -> Task:
    """
    Adds a human evaluation to a task and updates evaluation data for retrocompatibility
    """

    mongo_db = await get_mongo_db()

    if source is None:
        source = "owner"

    # Create the Evaluation object and store it in the db
    try:
        flag = cast(Literal["success", "failure"], human_eval)
        eval_data = Eval(
            project_id=task_model.project_id,
            session_id=task_model.session_id,
            task_id=task_model.id,
            value=flag,
            source=source,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create eval: {e}")

    await mongo_db["evals"].insert_one(eval_data.model_dump())

    # Update the task object
    try:
        update_payload: dict[str, object] = {}
        update_payload["flag"] = flag
        update_payload["last_eval"] = eval_data.model_dump()
        update_payload["human_eval"] = HumanEval(flag=human_eval).model_dump()
        update_payload["notes"] = notes
        await mongo_db["tasks"].update_one(
            {"id": task_model.id},
            {"$set": update_payload},
        )
        task_model.flag = flag
        task_model.last_eval = eval_data
        task_model.human_eval = HumanEval(flag=human_eval)
        task_model.notes = notes
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update Task {task_model.id}: {e}"
        )
    # Update the session object

    try:
        tasks = (
            await mongo_db["tasks"]
            .find({"session_id": task_model.session_id})
            .to_list(length=None)
        )
        nbr_success = 0
        nbr_failure = 0
        for task in tasks:
            logger.debug(f"Task {task}")
            validated_task = Task.model_validate(task)
            if (
                validated_task.human_eval is None
                or validated_task.human_eval.flag is None
            ):
                continue
            elif validated_task.human_eval.flag == "success":
                nbr_success += 1
            elif validated_task.human_eval.flag == "failure":
                nbr_failure += 1
        if nbr_success + nbr_failure == 0:
            session_flag = None
        elif nbr_success >= nbr_failure:
            session_flag = "success"
        else:
            session_flag = "failure"
        await mongo_db["sessions"].update_one(
            {"id": validated_task.session_id},
            {"$set": {"stats.human_eval": session_flag}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update Session {task_model.session_id}: {e}",
        )

    return task_model


async def update_task(
    task_model: Task,
    metadata: dict | None = None,
    data: dict | None = None,
    notes: str | None = None,
    flag: str | None = None,
    flag_source: str | None = None,
) -> Task:
    mongo_db = await get_mongo_db()

    # Update the task object if the fields are not None
    if metadata is not None:
        # Filter non-jsonable values
        metadata = filter_nonjsonable_keys(metadata)
        task_model.metadata = metadata
    if data is not None:
        task_model.data = data
    if notes is not None:
        task_model.notes = notes
    if flag is not None:
        task_model.flag = flag
        flag_source = flag_source
        if flag_source is None:
            flag_source = "user"
        # Create the Evaluation object and store it in the db
        flag = cast(Literal["success", "failure"], flag)
        eval_data = Eval(
            project_id=task_model.project_id,
            session_id=task_model.session_id,
            task_id=task_model.id,
            value=flag,
            source=flag_source,
        )
        await mongo_db["evals"].insert_one(eval_data.model_dump())
        task_model.last_eval = eval_data

    # Update the task object
    try:
        await mongo_db["tasks"].update_one(
            {"id": task_model.id}, {"$set": task_model.model_dump()}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update Task {task_model.id}: {e}"
        )

    return task_model


async def add_event_to_task(
    task: Task,
    event: EventDefinition,
    event_source: str = "owner",
    score_range_value: float | None = None,
    score_category_label: str | None = None,
) -> Task:
    """
    Adds an event to a task
    """
    mongo_db = await get_mongo_db()
    # Check if the event is already in the task
    if task.events is not None and event.event_name in [
        e.event_name for e in task.events
    ]:
        return task

    if (
        score_range_value is None
        and score_category_label is not None
        and event.score_range_settings.score_type == "category"
        and event.score_range_settings.categories is not None
    ):
        score_range_value = (
            event.score_range_settings.categories.index(score_category_label) + 1
        )
    if score_range_value is None:
        score_range = None
    else:
        score_range = ScoreRange(
            score_type=event.score_range_settings.score_type,
            min=event.score_range_settings.min,
            max=event.score_range_settings.max,
            label=score_category_label,
            value=score_range_value,
        )

    # Add the event to the events collection and to the task
    detected_event_data = Event(
        event_name=event.event_name,
        task_id=task.id,
        session_id=task.session_id,
        project_id=task.project_id,
        source=event_source,
        webhook=event.webhook,
        org_id=task.org_id,
        event_definition=event,
        confirmed=True,
        score_range=score_range,
    )
    await mongo_db["events"].insert_one(detected_event_data.model_dump())

    if task.events is None:
        task.events = []
    task.events.append(detected_event_data)

    return task


async def remove_event_from_task(task: Task, event_name: str) -> Task:
    """
    Removes an event from a task
    """
    mongo_db = await get_mongo_db()
    # Check if the event is in the task
    if task.events is not None and event_name in [e.event_name for e in task.events]:
        # Mark the event as removed in the events database
        await mongo_db["events"].update_many(
            {"task_id": task.id, "event_name": event_name},
            {
                "$set": {
                    "removed": True,
                    "removal_reason": "removed_by_user_from_session",
                }
            },
        )
        # Remove the event from the task
        task.events = [e for e in task.events if e.event_name != event_name]

    return task


async def get_total_nb_of_tasks(
    project_id: str,
    filters: ProjectDataFilters | None = None,
) -> int | None:
    """
    Get the total number of tasks of a project.
    """
    mongo_db = await get_mongo_db()

    if filters is None:
        filters = ProjectDataFilters()

    with_events = any(
        [
            filters.event_name is not None,
            filters.event_id is not None,
            filters.scorer_value is not None,
        ]
    )

    collection: Literal["tasks_with_events", "tasks"] = (
        "tasks_with_events" if with_events else "tasks"
    )

    query_builder = QueryBuilder(
        project_id=project_id,
        filters=filters,
        fetch_objects=collection,
    )
    pipeline = await query_builder.build()
    query_result = (
        await mongo_db[collection]
        .aggregate(
            pipeline
            + [
                {"$count": "nb_tasks"},
            ]
        )
        .to_list(length=1)
    )

    if len(query_result) == 0:
        return None

    total_nb_tasks = query_result[0]["nb_tasks"]
    return total_nb_tasks


async def label_sentiment_analysis(
    project_id: str,
    score_threshold: float | None = None,
    magnitude_threshold: float | None = None,
) -> None:
    """
    Label sentiment analysis for a project.
    """
    mongo_db = await get_mongo_db()

    if score_threshold is None:
        score_threshold = 0.5
    if magnitude_threshold is None:
        magnitude_threshold = 0.3

    _ = await mongo_db["tasks"].update_many(
        # This query matches all tasks beloging to the project_id and with a score higher than score_threshold
        {
            "project_id": project_id,
            "sentiment.score": {"$gt": score_threshold},
        },
        {
            "$set": {"sentiment.label": "positive"},
        },
    )
    _ = await mongo_db["tasks"].update_many(
        # This query matches all tasks beloging to the project_id and with a score lower than -score_threshold
        {
            "project_id": project_id,
            "sentiment.score": {"$lt": -score_threshold},
        },
        {
            "$set": {"sentiment.label": "negative"},
        },
    )
    _ = await mongo_db["tasks"].update_many(
        # This query matches all tasks beloging to the project_id and with a score between -score_threshold and score_threshold
        # It also filters out tasks with a magnitude higher than magnitude_threshold
        {
            "project_id": project_id,
            "sentiment.score": {"$gte": -score_threshold, "$lte": score_threshold},
            "sentiment.magnitude": {"$lt": magnitude_threshold},
        },
        {
            "$set": {"sentiment.label": "neutral"},
        },
    )
    _ = await mongo_db["tasks"].update_many(
        # This query matches all tasks beloging to the project_id and with a score between -score_threshold and score_threshold
        # It also filters out tasks with a magnitude higher than magnitude_threshold
        {
            "project_id": project_id,
            "sentiment.score": {"$gte": -score_threshold, "$lte": score_threshold},
            "sentiment.magnitude": {"$gte": magnitude_threshold},
        },
        {
            "$set": {"sentiment.label": "mixed"},
        },
    )

    return None


async def get_all_tasks(
    project_id: str,
    filters: ProjectDataFilters | None = None,
    get_events: bool = True,
    get_tests: bool = False,  # Unused, always False
    validate_metadata: bool = False,
    limit: int | None = None,
    pagination: Pagination | None = None,
    sorting: list[Sorting] | None = None,
) -> list[Task]:
    """
    Get all the tasks of a project.
    """

    mongo_db = await get_mongo_db()

    fetch_objects: Literal["tasks", "tasks_with_events"] = "tasks"
    if get_events and not pagination:
        fetch_objects = "tasks_with_events"

    query_builder = QueryBuilder(
        project_id=project_id,
        filters=filters,
        fetch_objects=fetch_objects,
    )
    pipeline = await query_builder.build()

    # Get rid of the raw_input and raw_output fields
    pipeline.append(
        {
            "$project": {
                "additional_input": 0,
                "additional_output": 0,
            }
        }
    )

    # To avoid the sort to OOM on Serverless MongoDB executor, we restrain the pipeline to the necessary fields...
    if sorting is None:
        sorting_dict = {"created_at": -1}
    else:
        sorting_dict = {sort.id: 1 if sort.desc else -1 for sort in sorting}
    pipeline.extend(
        [
            {
                "$project": {
                    "id": 1,
                    **{sort_key: 1 for sort_key in sorting_dict.keys()},
                }
            },
            {"$sort": sorting_dict},
        ]
    )

    # Add pagination
    if pagination:
        pipeline.extend(
            [
                {"$skip": pagination.page * pagination.per_page},
                {"$limit": pagination.per_page},
            ]
        )
        limit = None

    # ... and then we add the lookup and the deduplication
    pipeline.extend(
        [
            {
                "$lookup": {
                    "from": "tasks",
                    "localField": "id",
                    "foreignField": "id",
                    "as": "tasks",
                }
            },
            # unwind the tasks array
            {"$unwind": "$tasks"},
            # Replace the root with the tasks
            {"$replaceRoot": {"newRoot": "$tasks"}},
        ]
    )
    if get_events:
        query_builder.merge_events(foreignField="task_id", force=True)
        query_builder.deduplicate_tasks_events()

    tasks = await mongo_db["tasks"].aggregate(pipeline).to_list(length=limit)

    # Cast to tasks
    valid_tasks = [Task.model_validate(data) for data in tasks]

    if validate_metadata:
        for task in valid_tasks:
            # Remove the _id field from the task metadata
            if task.metadata is not None:
                task.metadata = filter_nonjsonable_keys(task.metadata)

    return valid_tasks


async def fetch_flattened_tasks(
    project_id: str,
    limit: int | None = 1000,
    pagination: Pagination | None = None,
    with_events: bool = True,
    with_sessions: bool = True,
    keep_removed_events: bool = False,
    sort_get_most_recent: bool = True,
    filters: ProjectDataFilters | None = None,
) -> list[FlattenedTask]:
    """
    Get a flattened representation of the tasks of a project for analytics.

    Parameters:
    - project_id: the project_id of the project.
    - limit parameter: the maximum number of tasks to return. Note: if with_events is True, as the result is flattened, the number of resulting
    rows can be higher than the limit (e.g. if a task has multiple events).
    - pagination parameter: to paginate the results. If pagination is provided, the limit parameter is ignored.
    Note: if with_events is True, the number of results can be higher than the per_page parameter of the pagination,
    as a task can have multiple events.
    - with_events parameter: if True, includes the events in the result.
    - with_sessions parameter: if True, includes the session information in the result.
    - keep_removed_events parameter allows to include the removed events in the result ; if with_events is False, this parameter is ignored.
    - sort_get_most_recent parameter: if True, the tasks are sorted by creation date in descending order.
    - filters parameter: filters to apply to the tasks.

    Returns:
    - A list of FlattenedTask objects.
    """

    if filters is None:
        filters = ProjectDataFilters()

    if not with_events and keep_removed_events:
        logger.warning(
            "The with_removed_events parameter is ignored if with_events is False"
        )

    # Create an aggregated table
    mongo_db = await get_mongo_db()

    # Aggregation pipeline
    query = QueryBuilder(
        fetch_objects="tasks",
        project_id=project_id,
        filters=filters,
    )
    pipeline = query.pipeline
    query.main_doc_filter_tasks()

    return_columns = {
        "task_id": "$id",
        "task_input": "$input",
        "task_output": "$output",
        "task_metadata": "$metadata",
        "task_eval": "$flag",
        "task_eval_source": "$last_eval.source",
        "task_eval_at": "$last_eval.created_at",
        "task_created_at": "$created_at",
        "session_id": "$session_id",
        "task_position": "$task_position",
    }
    # pipeline += [{"$project": return_columns}]

    # Sort the pipeline
    if sort_get_most_recent:
        pipeline += [{"$sort": {"created_at": -1}}]
    else:
        pipeline += [{"$sort": {"created_at": 1}}]

    if pagination:
        pipeline += [
            {"$skip": pagination.page * pagination.per_page},
            {"$limit": pagination.per_page},
        ]
    else:
        pipeline += [{"$limit": limit}]

    if with_sessions:
        query.merge_sessions(foreignField="task_id")
        pipeline.extend(
            [
                {
                    "$unwind": {
                        "path": "$sessions",
                        "preserveNullAndEmptyArrays": True,
                    }
                }
            ]
        )
        return_columns = {
            **return_columns,
            "session_length": "$sessions.session_length",
        }
        # pipeline += [{"$project": return_columns}]

    if with_events:
        query.merge_events(foreignField="task_id")
        query.deduplicate_tasks_events(keep_removed=keep_removed_events)
        pipeline += [
            {
                "$unwind": {
                    "path": "$events",
                    "preserveNullAndEmptyArrays": True,
                }
            }
        ]

        return_columns = {
            **return_columns,
            "event_id": "$events.id",
            "event_name": "$events.event_name",
            "event_created_at": "$events.created_at",
            "event_confirmed": "$events.confirmed",
            "event_score_range_value": "$events.score_range.value",
            "event_score_range_min": "$events.score_range.min",
            "event_score_range_max": "$events.score_range.max",
            "event_score_range_score_type": "$events.score_range.score_type",
            "event_score_range_label": "$events.score_range.label",
            "event_source": "$events.source",
            "event_categories": "$events.event_definition.score_range_settings.categories",
        }
        if keep_removed_events:
            return_columns = {
                **return_columns,
                "event_removed": "$events.removed",
                "event_removal_reason": "$events.removal_reason",
            }
        # pipeline += [{"$project": return_columns}]

    await query.task_complex_filters()
    pipeline += [{"$project": return_columns}]

    logger.info(f"Flatten task pipeline: {pipeline}")

    # Query Mongo
    flattened_tasks = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)

    logger.info(f"Got: {len(flattened_tasks)} results")

    new_flattened_tasks = []
    for task in flattened_tasks:
        # Remove the _id field
        if "_id" in task.keys():
            del task["_id"]

        # Flatten the task_metadata field into multiple task_metadata.{key} fields
        if "task_metadata" in task.keys():
            for key, value in task["task_metadata"].items():
                if not isinstance(value, dict) and not isinstance(value, list):
                    task[f"task_metadata.{key}"] = value
                else:
                    # TODO: Handle nested fields. For now, cast to string
                    task[f"task_metadata.{key}"] = str(value)
            del task["task_metadata"]
        # Convert to a FlattenedTask model
        new_task = FlattenedTask.model_validate(task)
        new_flattened_tasks.append(new_task)

    logger.info(f"Returning: {len(new_flattened_tasks)} unnested results")

    return new_flattened_tasks


async def update_from_flattened_tasks(
    org_id: str,
    project_id: str,
    flattened_tasks: list[FlattenedTask],
) -> bool:
    """
    Update the tasks of a project from a flattened representation.
    Used in combination with get_flattened_tasks

    Supported flat fields:

    task_id
    task_metadata
    task_eval
    task_eval_source
    task_eval_at

    TODO: Add support for updating the events
    """

    # Verify that all the task_id belong to the project_id
    mongo_db = await get_mongo_db()
    project_ids_in_db = (
        await mongo_db["tasks"]
        .aggregate(
            [
                {"$match": {"id": {"$in": [task.task_id for task in flattened_tasks]}}},
                {"$project": {"project_id": 1}},
            ]
        )
        .to_list(length=2)
    )
    # Compute the intersection of the project_ids
    project_ids_in_db = {project_id["project_id"] for project_id in project_ids_in_db}
    # If the intersection is not empty, it means that the task_id belong to another project
    if project_ids_in_db - {project_id} != set():
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to tasks not in project {project_id}",
        )

    # A single row is a combination of task x event x eval
    # TODO : Infer the granularity from the available non-None columns

    task_update: dict[str, dict[str, object]] = defaultdict(dict)
    eval_create_statements = []
    for task in flattened_tasks:
        if getattr(task, "task_metadata") is not None:
            task_update[task.task_id]["metadata"] = getattr(task, "task_metadata")
        if task.task_eval is not None and task.task_eval in ["success", "failure"]:
            task_update[task.task_id]["flag"] = task.task_eval
            last_eval = Eval(
                org_id=org_id,
                project_id=project_id,
                value=task.task_eval,
                session_id=task.session_id,
                task_id=task.task_id,
                source="owner",
            )
            # Override source and created_at if provided
            if task.task_eval_source is not None:
                last_eval.source = task.task_eval_source
            if task.task_eval_at is not None:
                last_eval.created_at = task.task_eval_at
            task_update[task.task_id]["last_eval"] = last_eval.model_dump()
            eval_create_statements.append(
                InsertOne(
                    last_eval.model_dump(),
                )
            )

    # Reformat the list into a list of UpdateOne or DeleteOne
    tasks_update_statements = [
        UpdateOne(
            {"id": task_id, "project_id": project_id},
            {"$set": values_to_update},
        )
        for task_id, values_to_update in task_update.items()
    ]

    # Execute the update
    if tasks_update_statements:
        tasks_results = await mongo_db["tasks"].bulk_write(tasks_update_statements)
    if eval_create_statements:
        eval_results = await mongo_db["evals"].bulk_write(eval_create_statements)

    return tasks_results.modified_count > 0 or eval_results.inserted_count > 0

import datetime
from typing import Dict, List, Literal, Optional

from app.db.mongo import get_mongo_db

from phospho.models import ProjectDataFilters
from loguru import logger


class QueryBuilder:
    """
    Class to build common MongoDB queries
    """

    project_id: Optional[str] = None
    pipeline: List[Dict[str, object]]
    fetch_object: Literal[
        "tasks",
        "sessions",
        "tasks_with_events",
        "sessions_with_events",
        "sessions_with_tasks",
    ]
    filters: ProjectDataFilters

    def __init__(
        self,
        fetch_objects: Literal[
            "tasks",
            "sessions",
            "tasks_with_events",
            "sessions_with_events",
            "sessions_with_tasks",
        ],
        project_id: Optional[str] = None,
        filters: Optional[ProjectDataFilters] = None,
    ):
        """
        Create a new QueryBuilder instance.

        Note: The filter "is_last_task" is not supported for sessions, sessions_with_events and sessions_with_tasks.
            It's also very slow for tasks, as it requires a full scan of the tasks collection.
            TODO: Fix this using the extractor.

        Args:
            fetch_objects (str): The object to fetch.
            project_id (str): The project_id to filter on.
            filters (ProjectDataFilters): The filters to apply to the query.
        """
        self.pipeline = []
        self.project_id = project_id
        self.fetch_object = fetch_objects
        if filters is None:
            filters = ProjectDataFilters()
        self.filters = filters

    def merge_events(
        self, foreignField: Literal["task_id", "session_id"], force: bool = False
    ) -> None:
        """
        Merge the events in the pipeline.

        Used for filtering on events and fetching them.
        """
        # if already merged, return the pipeline
        if not force and any(
            operator.get("$lookup", {}).get("from") == "events"  # type: ignore
            for operator in self.pipeline
        ):
            return
        else:
            self.pipeline += [
                {
                    "$lookup": {
                        "from": "events",
                        "localField": "id",
                        "foreignField": foreignField,
                        "as": "events",
                    },
                },
            ]

    def merge_tasks(
        self, foreignField: Literal["session_id"] = "session_id", force: bool = False
    ) -> None:
        """
        Merge the tasks in the pipeline.

        Used for complex filtering on sessions (e.g. filtering on the user_id of the tasks)
        """
        # if already merged, return the pipeline
        if not force and any(
            operator.get("$lookup", {}).get("from") == "tasks"  # type: ignore
            for operator in self.pipeline
        ):
            return
        else:
            self.pipeline += [
                {
                    "$lookup": {
                        "from": "tasks",
                        "localField": "id",
                        "foreignField": foreignField,
                        "as": "tasks",
                    },
                },
            ]

    def _main_doc_filter(self, prefix: str = "") -> Dict[str, object]:
        """
        Implements:
        - project_id
        - created_at
        """
        if prefix != "" and not prefix.endswith("."):
            # Add a dot at the end of the prefix if it is not already there
            prefix += "."

        filters = self.filters

        match: Dict[str, object] = {}

        # if there is no match project_id in the pipeline
        if self.project_id and not any(
            operator.get("$match", {}).get(f"{prefix}project_id") == self.project_id
            for operator in self.pipeline
        ):
            match[f"{prefix}project_id"] = self.project_id

        # Cast the created_at filters to int
        if isinstance(filters.created_at_start, datetime.datetime):
            filters.created_at_start = int(filters.created_at_start.timestamp())
        if isinstance(filters.created_at_end, datetime.datetime):
            filters.created_at_end = int(filters.created_at_end.timestamp())

        if filters.created_at_start is not None:
            match[f"{prefix}created_at"] = {"$gte": filters.created_at_start}
        if filters.created_at_end is not None:
            match[f"{prefix}created_at"] = {
                **match.get(f"{prefix}created_at", {}),
                "$lte": filters.created_at_end,
            }

        return match

    def main_doc_filter_tasks(self, prefix: str = "") -> Dict[str, object]:
        """
        Implements:
        - project_id
        - created_at
        - last_eval_source
        - version_id
        - language
        - sentiment
        - flag
        - has_notes
        - sessions_ids
        - tasks_ids
        - metadata
        - user_id
        """
        filters = self.filters
        match: Dict[str, object] = self._main_doc_filter(prefix=prefix)

        # if (
        #     self.fetch_object == "tasks"
        #     or self.fetch_object == "tasks_with_events"
        #     or prefix == "tasks."
        # ):
        #     match[f"{prefix}test_id"] = None

        if filters.last_eval_source is not None:
            if filters.last_eval_source.startswith("phospho"):
                # We want to filter on the source starting with "phospho"
                match[f"{prefix}last_eval.source"] = {"$regex": "^phospho"}
            else:
                # We want to filter on the source not starting with "phospho"
                match[f"{prefix}last_eval.source"] = {"$regex": "^(?!phospho).*"}

        if filters.version_id is not None:
            match[f"{prefix}metadata.version_id"] = filters.version_id

        if filters.language is not None:
            match[f"{prefix}language"] = filters.language

        if filters.sentiment is not None:
            match[f"{prefix}sentiment.label"] = filters.sentiment

        if filters.flag is not None:
            # match[f"{prefix}flag"] = filters.flag
            match["$or"] = [
                {f"{prefix}flag": filters.flag},
                {f"{prefix}human_eval.flag": filters.flag},
            ]

        if filters.has_notes is not None and filters.has_notes:
            match["$and"] = [
                {f"{prefix}notes": {"$exists": True}},
                {f"{prefix}notes": {"$ne": None}},
                {f"{prefix}notes": {"$ne": ""}},
            ]

        if filters.sessions_ids is not None:
            if len(filters.sessions_ids) == 1:
                match[f"{prefix}session_id"] = filters.sessions_ids[0]
            elif len(filters.sessions_ids) > 1:
                match[f"{prefix}session_id"] = {"$in": filters.sessions_ids}

        if filters.tasks_ids is not None:
            if len(filters.tasks_ids) == 1:
                match[f"{prefix}id"] = filters.tasks_ids[0]
            elif len(filters.tasks_ids) > 1:
                match[f"{prefix}id"] = {"$in": filters.tasks_ids}

        if filters.metadata is not None:
            for key, value in filters.metadata.items():
                match[f"{prefix}metadata.{key}"] = value

        if filters.user_id is not None:
            match[f"{prefix}metadata.user_id"] = filters.user_id

        if match:
            self.pipeline.append({"$match": match})

        return match

    def main_doc_filter_sessions(self, prefix: str = "") -> Dict[str, object]:
        """
        Implements:
        - project_id
        - created_at
        - version_id
        - language
        - sentiment
        - flag
        - sessions_ids
        - tasks_ids

        Not supported:
        - has_notes
        """
        filters = self.filters
        match: Dict[str, object] = self._main_doc_filter(prefix=prefix)

        if filters.version_id is not None:
            # TODO: Check if we need to filter on the version_id of the session or the version_id of the tasks
            match["metadata.version_id"] = filters.version_id

        if filters.language is not None:
            match["stats.most_common_language"] = filters.language

        if filters.sentiment is not None:
            match["stats.most_common_sentiment_label"] = filters.sentiment

        if filters.flag is not None:
            match["$or"] = [
                {"stats.human_eval": filters.flag},
                {"stats.most_common_flag": filters.flag},
            ]

        # if filters.has_notes is not None and filters.has_notes:
        #     match["$and"] = [
        #         {f"{prefix}notes": {"$exists": True}},
        #         {f"{prefix}notes": {"$ne": None}},
        #         {f"{prefix}notes": {"$ne": ""}},
        #     ]

        if filters.sessions_ids is not None:
            if len(filters.sessions_ids) == 1:
                match["id"] = filters.sessions_ids[0]
            elif len(filters.sessions_ids) > 1:
                match["id"] = {"$in": filters.sessions_ids}

        if filters.tasks_ids is not None:
            if len(filters.tasks_ids) == 1:
                match["tasks.id"] = filters.tasks_ids[0]
            elif len(filters.tasks_ids) > 1:
                match["task_id"] = {"$in": filters.tasks_ids}

        if match:
            self.pipeline.append({"$match": match})

        return match

    async def task_complex_filters(self, prefix: str = "") -> Dict[str, object]:
        """
        More complex filters for tasks that require fetching data from the database
        or intermediate pipeline stages. This mutates the pipeline.

        Implements:
        - event_name
        - event_id
        - clustering_id
        - clusters_ids
        - is_last_task # TODO: Refacto so that a main_doc_filter can handle this
        """

        filters = self.filters
        match: Dict[str, object] = {}

        if filters.event_name is not None:
            self.merge_events(foreignField="task_id")
            match["$and"] = [
                {f"{prefix}events": {"$ne": []}},
                {
                    f"{prefix}events": {
                        "$elemMatch": {"event_name": {"$in": filters.event_name}}
                    }
                },
            ]

        if filters.event_id is not None:
            self.merge_events(foreignField="task_id")
            match["$and"] = [
                {f"{prefix}events": {"$ne": []}},
                {f"{prefix}events": {"$elemMatch": {"id": {"$in": filters.event_id}}}},
            ]

        if filters.clustering_id is not None and filters.clusters_ids is None:
            # Fetch the clusterings
            mongo_db = await get_mongo_db()
            clustering = await mongo_db["private-clusterings"].find_one(
                {"id": filters.clustering_id}
            )
            if clustering:
                filters.clusters_ids = []
                filters.clusters_ids.extend(clustering.get("clusters_ids", []))

        if filters.clusters_ids is not None:
            # Fetch the cluster
            mongo_db = await get_mongo_db()
            clusters = (
                await mongo_db["private-clusters"]
                .find({"id": {"$in": filters.clusters_ids}})
                .to_list(length=None)
            )
            if clusters:
                new_task_ids = []
                for cluster in clusters:
                    new_task_ids.extend(cluster.get("tasks_ids", []))
                current_task_ids = match.get(f"{prefix}id", {"$in": []})["$in"]
                if current_task_ids:
                    # Do the intersection of the current task ids and the new task ids
                    new_task_ids = list(
                        set(current_task_ids).intersection(new_task_ids)
                    )
                match[f"{prefix}id"] = {"$in": new_task_ids}

        if filters.is_last_task is not None:
            # TODO: Compute this dynamically in the session processing pipeline
            logger.debug("FILTER: is last task")
            from copy import copy

            from app.services.mongo.sessions import compute_task_position

            filters_without_latest = copy(filters)
            filters_without_latest.is_last_task = None

            logger.debug("Computing task position...")
            if self.project_id:
                await compute_task_position(
                    project_id=self.project_id, filters=filters_without_latest
                )
            match[f"{prefix}is_last_task"] = filters.is_last_task

        if match:
            self.pipeline.append({"$match": match})

        return match

    async def session_complex_filters(self) -> Dict[str, object]:
        """
        More complex filters for sessions that require fetching data from the database
        or intermediate pipeline stages. This mutates the pipeline.

        Implements:
        - event_name
        - event_id
        - clustering_id
        - clusters_ids
        - user_id
        - metadata (filter on the Task's metadata)

        Not supported:
        - is_last_task
        """

        filters = self.filters

        match: Dict[str, object] = {}

        if filters.event_name is not None:
            self.merge_events(foreignField="session_id")
            match["$and"] = [
                {"events": {"$ne": []}},
                {
                    "events": {
                        "$elemMatch": {
                            "event_name": {"$in": filters.event_name},
                        }
                    }
                },
            ]

        if filters.event_id is not None:
            self.merge_events(foreignField="session_id")
            match["$and"] = [
                {"events": {"$ne": []}},
                {
                    "events": {
                        "$elemMatch": {
                            "id": {"$in": filters.event_id},
                        }
                    }
                },
            ]

        if filters.clustering_id is not None and filters.clusters_ids is None:
            # Fetch the clusterings
            mongo_db = await get_mongo_db()
            clustering = await mongo_db["private-clusterings"].find_one(
                {"id": filters.clustering_id}
            )
            if clustering:
                filters.clusters_ids = []
                filters.clusters_ids.extend(clustering.get("clusters_ids", []))

        if filters.clusters_ids is not None:
            # Fetch the cluster
            mongo_db = await get_mongo_db()
            clusters = (
                await mongo_db["private-clusters"]
                .find({"id": {"$in": filters.clusters_ids}})
                .to_list(length=None)
            )
            if clusters:
                new_sessions_ids = []
                for cluster in clusters:
                    new_sessions_ids.extend(cluster.get("sessions_ids", []))
                current_sessions_ids = match.get("id", {"$in": []})["$in"]
                if current_sessions_ids:
                    # Do the intersection of the current task ids and the new task ids
                    new_sessions_ids = list(
                        set(current_sessions_ids).intersection(new_sessions_ids)
                    )
                match["id"] = {"$in": new_sessions_ids}

        if filters.user_id is not None:
            self.merge_tasks()
            match["tasks.metadata.user_id"] = filters.user_id

        # Filter on the Task's metadata
        if filters.metadata is not None:
            self.merge_tasks()
            for key, value in filters.metadata.items():
                match[f"metadata.{key}"] = value

        if match:
            self.pipeline.append({"$match": match})

        return match

    def deduplicate_tasks_events(self) -> None:
        self.pipeline += [
            {
                "$addFields": {
                    "events": {
                        "$filter": {
                            "input": "$events",
                            "as": "event",
                            "cond": {
                                "$and": [
                                    {
                                        "$ne": [
                                            "$$event.removed",
                                            True,
                                        ],
                                    },
                                    {
                                        "$or": [
                                            # The field is present in the event definition and the task
                                            {
                                                "$and": [
                                                    {
                                                        "$eq": [
                                                            "$$event.event_definition.is_last_task",
                                                            True,
                                                        ]
                                                    },
                                                    {
                                                        "$eq": [
                                                            "$is_last_task",
                                                            True,
                                                        ]
                                                    },
                                                ]
                                            },
                                            # the field is not present in the event definition
                                            {
                                                "$not": [
                                                    "$$event.event_definition.is_last_task",
                                                ]
                                            },
                                        ],
                                    },
                                ]
                            },
                        }
                    }
                }
            },
            {
                "$set": {
                    "events": {
                        "$reduce": {
                            "input": "$events",
                            "initialValue": [],
                            "in": {
                                "$concatArrays": [
                                    "$$value",
                                    {
                                        "$cond": [
                                            {
                                                "$in": [
                                                    "$$this.event_definition.id",
                                                    "$$value.event_definition.id",
                                                ]
                                            },
                                            [],
                                            ["$$this"],
                                        ]
                                    },
                                ]
                            },
                        }
                    },
                }
            },
        ]

    def deduplicate_sessions_events(self) -> None:
        self.pipeline += [
            {
                "$addFields": {
                    "events": {
                        "$filter": {
                            "input": "$events",
                            "as": "event",
                            "cond": {"$ne": ["$$event.removed", True]},
                        }
                    }
                }
            },
            # Remove duplicates
            {
                "$set": {
                    "events": {
                        "$reduce": {
                            "input": "$events",
                            "initialValue": [],
                            "in": {
                                "$concatArrays": [
                                    "$$value",
                                    {
                                        "$cond": [
                                            {
                                                "$in": [
                                                    "$$this.event_definition.id",
                                                    "$$value.event_definition.id",
                                                ]
                                            },
                                            [],
                                            ["$$this"],
                                        ]
                                    },
                                ]
                            },
                        }
                    },
                }
            },
        ]

    async def build(self) -> List[Dict[str, object]]:
        """
        Build the pipeline for the query.
        Edits in-place the pipeline attribute of the class.
        """

        # Each query type has its own sequence of operations
        # This is done to be more efficient and avoid unnecessary operations

        if self.fetch_object == "tasks":
            self.main_doc_filter_tasks()
            await self.task_complex_filters()

        elif self.fetch_object == "tasks_with_events":
            self.main_doc_filter_tasks()
            await self.task_complex_filters()
            self.merge_events(foreignField="task_id")
            self.deduplicate_tasks_events()

        elif self.fetch_object == "sessions":
            self.main_doc_filter_sessions()
            await self.session_complex_filters()

        elif self.fetch_object == "sessions_with_events":
            self.main_doc_filter_sessions()
            await self.session_complex_filters()
            self.merge_events(foreignField="session_id")
            self.deduplicate_sessions_events()

        elif self.fetch_object == "sessions_with_tasks":
            self.main_doc_filter_sessions()
            await self.session_complex_filters()
            self.merge_tasks()
            self.main_doc_filter_tasks()
            await self.task_complex_filters()

        elif self.fetch_object == "sessions_with_events_and_tasks":
            self.main_doc_filter_sessions()
            await self.session_complex_filters()
            self.merge_events(foreignField="session_id")
            self.deduplicate_sessions_events()
            # Note: we don't merge Tasks' events
            self.merge_tasks()
            self.main_doc_filter_tasks()
            await self.task_complex_filters()

        else:
            raise ValueError(f"Unsupported fetch_object: {self.fetch_object}")

        return self.pipeline

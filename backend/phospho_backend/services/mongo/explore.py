"""
Explore metrics service
"""

import datetime
import math
import numpy as np
from collections import defaultdict
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast

import pandas as pd  # type: ignore
import pydantic
from phospho_backend.api.platform.models import ABTest
from phospho_backend.db.mongo import get_mongo_db
from phospho_backend.services.mongo.clustering import (
    get_date_last_clustering_timestamp,
    get_last_clustering_composition,
)
from phospho_backend.services.mongo.events import get_all_events
from phospho_backend.services.mongo.query_builder import QueryBuilder
from phospho_backend.services.mongo.tasks import (
    get_all_tasks,
    get_total_nb_of_tasks,
)
from phospho_backend.utils import generate_timestamp, get_last_week_timestamps
from loguru import logger
from sklearn.metrics import (  # type: ignore
    f1_score,
    precision_score,
    r2_score,
    recall_score,
    root_mean_squared_error,
)

from phospho.models import Event, ProjectDataFilters


async def project_has_tasks(project_id: str) -> bool:
    """
    Check if a project has tasks. This service should be super fast.
    Approximations are ok.
    """
    mongo_db = await get_mongo_db()
    doc = await mongo_db["tasks"].find_one({"project_id": project_id})
    return doc is not None


async def project_has_sessions(project_id: str) -> bool:
    """
    Check if a project has sessions. This service should be super fast.
    Approximations are ok.
    """
    mongo_db = await get_mongo_db()
    doc = await mongo_db["sessions"].find_one({"project_id": project_id})
    return doc is not None


async def project_has_enough_labelled_tasks(project_id: str, enough: int = 1) -> int:
    """
    Check if a project has enough labelled tasks, where enough is a number (eg: 10)
    This is used to display the "Not enough data" message on the dashboard.

    This service should be super fast. Approximations are ok.

    Returns: min(enough + 1, total number of labelled tasks)
    """
    mongo_db = await get_mongo_db()
    doc = (
        await mongo_db["tasks"]
        .find(
            {
                "project_id": project_id,
                "last_eval.source": {"$not": {"$regex": "^phospho"}},
                "last_eval": {"$ne": None},
            },
            # this is a hack to avoid counting all the documents
        )
        .to_list(length=enough + 1)
    )
    if doc is None:
        return 0
    return len(doc)


async def deprecated_get_dashboard_aggregated_metrics(
    project_id: str,
    index: List[Literal["days", "minutes"]],
    columns: List[Literal["event_name", "flag"]],
    count_of: Optional[Literal["tasks", "events"]] = "tasks",
    timerange: Optional[Literal["last_7_days", "last_30_minutes"]] = "last_7_days",
    filters: Optional[ProjectDataFilters] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, object]]:
    """
    Get aggregated metrics for a project. Used for dashboard.

    Note: the timerange parameter overrides the created_at_start and created_at_end
    parameters of the tasks_filter and events_filter.
    """

    timerange_start = None
    timerange_end = None

    if timerange == "last_7_days":
        timerange_end_datetime = datetime.datetime.now(datetime.timezone.utc)
        timerange_end = int(timerange_end_datetime.timestamp())
        timerange_start_datetime = timerange_end_datetime - datetime.timedelta(days=6)
        # Round to the beginning of the day
        timerange_start_datetime = timerange_start_datetime.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        timerange_start = int(timerange_start_datetime.timestamp())
    elif timerange == "last_30_minutes":
        timerange_end = generate_timestamp()
        timerange_start = timerange_end - 29 * 60

    # Override the created_at_start and created_at_end parameters
    # of the tasks_filter and events_filter if the timerange is set
    if timerange is not None:
        if filters is not None:
            filters.created_at_start = timerange_start
            filters.created_at_end = timerange_end
        else:
            filters = ProjectDataFilters(
                created_at_start=timerange_start,
                created_at_end=timerange_end,
                event_name=None,
                flag=None,
                last_eval_source=None,
                metadata=None,
            )

    # Fetch the data
    if count_of == "tasks":
        if filters is None:
            filters = ProjectDataFilters()
        if isinstance(filters.event_name, str):
            filters.event_name = [filters.event_name]
        tasks = await get_all_tasks(project_id=project_id, limit=limit, filters=filters)
        df = pd.DataFrame([task.model_dump() for task in tasks])
    if count_of == "events":
        events = await get_all_events(
            project_id=project_id,
            limit=limit,
            filters=filters,
        )
        df = pd.DataFrame([event.model_dump() for event in events])

    if not df.empty:
        # Convert the created_at column to datetime, assuming timestamp stored in UTC
        df["created_at"] = pd.to_datetime(df["created_at"], unit="s", utc=True)
        if index:
            if "days" in index:
                df["days"] = df["created_at"].dt.date
            if "minutes" in index:
                df["minutes"] = df["created_at"].dt.floor("min")

        # Aggregate
        df = df.pivot_table(
            values="id",
            index=index,
            columns=columns,
            aggfunc="count",
        ).reset_index()

    # For the last 7 days, fill the missing days with 0
    if timerange is not None:
        # Convert the timerange to datetime, assuming timestamp stored in UTC
        if timerange_start is not None:
            ts = datetime.datetime.fromtimestamp(timerange_start, datetime.timezone.utc)
        if timerange_end is not None:
            te = datetime.datetime.fromtimestamp(timerange_end, datetime.timezone.utc)

    if timerange == "last_7_days" and "days" in index:
        complete_date_range = pd.date_range(ts, te, freq="D")
        complete_df = pd.DataFrame({"days": complete_date_range})
        # Merge based on the calendar date part
        complete_df["days"] = pd.to_datetime(complete_df["days"]).dt.date
        if not df.empty:
            df = pd.merge(complete_df, df, on="days", how="left")
        else:
            df = complete_df
            df[columns] = 0
        df = df.fillna(0)
    # For the last 30 minutes, fill the missing minutes with 0
    if timerange == "last_30_minutes" and "minutes" in index:
        complete_date_range = pd.date_range(ts, te, freq="min")
        complete_df = pd.DataFrame({"minutes": complete_date_range})
        # Merge based on the calendar date part
        complete_df["minutes"] = pd.to_datetime(complete_df["minutes"]).dt.floor("min")
        if not df.empty:
            df = pd.merge(complete_df, df, on="minutes", how="left")
        else:
            df = complete_df
            df[columns] = 0
        # Fill NaNs with 0
        df = df.fillna(0)

    if not df.empty:
        # Add columns with the date in ISO format
        df_dict = df.to_dict(orient="records")
    else:
        df_dict = []
    return cast(List[Dict[str, object]], df_dict)


async def get_success_rate_per_task_position(
    project_id,
    filters: ProjectDataFilters,
    quantile_filter: Optional[float] = None,
    **kwargs,
) -> Optional[List[Dict[str, object]]]:
    """
    Compute the success rate per message position. Used for the Tasks and the Sessions dashboard.
    We only keep the 90% percentile of the messages length to avoid outliers with very long sessions.

    Return None if there is no session_id in the tasks.
    """
    mongo_db = await get_mongo_db()
    collection_name = "sessions"

    # Ignore the flag filter
    filters.flag = None

    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="sessions_with_tasks",
        filters=filters,
    )
    pipeline = await query_builder.build()

    result = (
        await mongo_db[collection_name]
        .aggregate(
            pipeline
            + [
                # Order the tasks by created_at
                {
                    "$set": {
                        "tasks": {
                            "$sortArray": {
                                "input": "$tasks",
                                "sortBy": {"tasks.created_at": 1},
                            },
                        }
                    }
                },
                # Transform to get 1 doc = 1 task. We also add the task position.
                {"$unwind": {"path": "$tasks", "includeArrayIndex": "task_position"}},
                # Add a field "is_success" to the task
                {
                    "$set": {
                        "is_success": {
                            "$cond": [{"$eq": ["$tasks.flag", "success"]}, 1, 0]
                        }
                    }
                },
                # Group on the task position
                {
                    "$group": {
                        "_id": "$task_position",
                        "count": {"$count": {}},
                        "nb_success": {"$sum": "$is_success"},
                        "success_rate": {"$avg": "$is_success"},
                    }
                },
                # Add 1 to _id to start at 1
                {"$addFields": {"_id": {"$add": ["$_id", 1]}}},
                {"$sort": {"_id": 1}},
                {
                    "$project": {
                        "_id": 0,
                        "task_position": "$_id",
                        "count": 1,
                        "nb_success": 1,
                        "success_rate": 1,
                    }
                },
            ]
        )
        .to_list(length=None)
    )

    if len(result) == 0:
        return None

    success_rate_per_message_position = pd.DataFrame(result)

    # Filter on field "task_position" to keep only the 90% percentile
    if quantile_filter is not None:
        quantile = success_rate_per_message_position["task_position"].quantile(
            quantile_filter
        )
        success_rate_per_message_position = success_rate_per_message_position[
            success_rate_per_message_position["task_position"] <= quantile
        ]

    max_task_position = success_rate_per_message_position["task_position"].max()

    # # Add missing positions (propagate latest value)
    complete_positions = pd.DataFrame(
        {"task_position": range(1, max_task_position + 1)}
    )
    success_rate_per_message_position = pd.merge(
        complete_positions,
        success_rate_per_message_position,
        on="task_position",
        how="left",
    ).ffill()

    success_rate_per_message_position_dict = success_rate_per_message_position[
        ["task_position", "success_rate"]
    ].to_dict(orient="records")
    return cast(List[Dict[str, object]], success_rate_per_message_position_dict)


async def get_total_success_rate(
    project_id: str,
    filters: ProjectDataFilters,
    **kwargs,
) -> Optional[float]:
    """
    Get the total success rate of a project. This is the ratio of successful tasks over
    the total number of tasks.
    """

    mongo_db = await get_mongo_db()
    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="tasks",
        filters=filters,
    )
    pipeline = await query_builder.build()

    # Add the success rate computation
    pipeline.extend(
        [
            {
                "$addFields": {
                    "is_success": {
                        "$sum": {"$cond": [{"$eq": ["$flag", "success"]}, 1, 0]}
                    }
                }
            },
            {"$group": {"_id": None, "global_success_rate": {"$avg": "$is_success"}}},
            {"$project": {"_id": 0, "global_success_rate": 1}},
        ]
    )
    # Query
    result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=1)
    if len(result) == 0:
        # No tasks = success rate is None
        return None
    total_success_rate = result[0]["global_success_rate"]
    return total_success_rate


async def get_most_detected_tagger_name(
    project_id: str,
    flag: Optional[Literal["success", "failure"]] = None,
    event_name: Optional[Union[str, List[str]]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
    sentiment: Optional[str] = None,
    last_eval_source: Optional[str] = None,
    language: Optional[str] = None,
    metadata: Optional[Dict[str, object]] = None,
    **kwargs,
) -> Optional[str]:
    """
    Get the most detected tagger name for a project.
    """
    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {
        "project_id": project_id,
        "removed": {"$ne": True},
        "event_definition.score_range_settings.score_type": "confidence",
    }
    # Filter on the event name
    if event_name is not None:
        main_filter["event_name"] = {"$in": event_name}
    # Time range filter
    if created_at_start is not None:
        main_filter["created_at"] = {"$gte": created_at_start}
    if created_at_end is not None:
        main_filter["created_at"] = {
            **main_filter.get("created_at", {}),  # type: ignore
            "$lte": created_at_end,
        }
    # Event is not removed
    main_filter["removed"] = {"$ne": True}
    pipeline: List[Dict[str, object]] = [
        {"$match": main_filter},
        {
            "$lookup": {
                "from": "tasks",
                "localField": "task_id",
                "foreignField": "id",
                "as": "tasks",
            },
        },
    ]
    tasks_filter: Dict[str, object] = {}
    # Filter on flag
    if flag is not None:
        tasks_filter["tasks.flag"] = flag
    # Filter on sentiment
    if sentiment is not None:
        tasks_filter["tasks.sentiment.label"] = sentiment
    # Filter on language
    if language is not None:
        tasks_filter["tasks.language"] = language
    # Filter on task metadata
    if metadata is not None:
        for key, value in metadata.items():
            tasks_filter[f"tasks.metadata.{key}"] = value
    # Last eval source filter
    if last_eval_source is not None:
        if last_eval_source.startswith("phospho"):
            # We want to filter on the source starting with "phospho"
            tasks_filter["tasks.last_eval.source"] = {"$regex": "^phospho"}
        else:
            # We want to filter on the source not starting with "phospho"

            tasks_filter["tasks.last_eval.source"] = {"$regex": "^(?!phospho).*"}

    if tasks_filter != {}:
        pipeline.append(
            {"$match": tasks_filter},
        )

    pipeline.extend(
        [
            # Deduplicate the events by task_id and event_name
            {"$group": {"_id": {"task_id": "$task_id", "event_name": "$event_name"}}},
            {"$group": {"_id": "$_id.event_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1},
        ]
    )
    result = await mongo_db["events"].aggregate(pipeline).to_list(length=1)
    if len(result) == 0:
        return None

    most_detected_event_name = result[0]["_id"]
    return most_detected_event_name


def extract_date_range(
    filters: ProjectDataFilters,
) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
    start_date = end_date = None
    if filters.created_at_start and isinstance(filters.created_at_start, int):
        start_date = datetime.datetime.fromtimestamp(filters.created_at_start)
    if filters.created_at_end and isinstance(filters.created_at_end, int):
        end_date = datetime.datetime.fromtimestamp(filters.created_at_end)

    if filters.created_at_start and isinstance(
        filters.created_at_start, datetime.datetime
    ):
        start_date = filters.created_at_start
    if filters.created_at_end and isinstance(filters.created_at_end, datetime.datetime):
        end_date = filters.created_at_end

    return start_date, end_date


def generate_date_range(
    start_date: datetime.datetime, end_date: datetime.datetime, time_dimension: str
) -> List[str]:
    date_list = []
    current_date = start_date

    while current_date <= end_date:
        if time_dimension == "minute":
            date_list.append(current_date.strftime("%Y-%m-%d %H:%M"))
            current_date += datetime.timedelta(minutes=1)
        elif time_dimension == "hour":
            date_list.append(current_date.strftime("%Y-%m-%d %H"))
            current_date += datetime.timedelta(hours=1)
        elif time_dimension == "day":
            date_list.append(current_date.strftime("%Y-%m-%d"))
            current_date += datetime.timedelta(days=1)
        elif time_dimension == "month":
            date_list.append(current_date.strftime("%Y-%m"))
            current_date = (
                current_date.replace(day=1) + datetime.timedelta(days=32)
            ).replace(day=1)

    return date_list


async def get_nb_of_daily_tasks(
    project_id: str,
    filters: ProjectDataFilters,
    **kwargs,
) -> List[dict]:
    """
    Get the number of daily tasks of a project.
    """
    # tasks = await get_all_tasks(project_id=project_id, limit=None, filters=filters)

    mongo_db = await get_mongo_db()

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
        fetch_objects=collection,
        filters=filters,
    )
    pipeline = await query_builder.build()
    # Group by date
    pipeline.extend(
        [
            # Transform the created_at field to a date
            {
                "$addFields": {
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": {"$toDate": {"$multiply": ["$created_at", 1000]}},
                        }
                    }
                }
            },
            {"$group": {"_id": "$date", "nb_tasks": {"$sum": 1}}},
            {"$project": {"_id": 0, "date": "$_id", "nb_tasks": 1}},
            {"$sort": {"date": 1}},
        ]
    )

    result = await mongo_db[collection].aggregate(pipeline).to_list(length=None)
    if len(result) == 0:
        return []

    # Add missing days in the date range
    result_df = pd.DataFrame(result)
    start_date_range, end_date_range = extract_date_range(filters)
    if start_date_range is None:
        if not result_df.empty:
            start_date_range = result_df["date"].min()
        else:
            start_date_range = datetime.datetime.now()
    if end_date_range is None:
        end_date_range = datetime.datetime.now()

    complete_date_range = pd.date_range(start_date_range, end_date_range, freq="D")
    complete_df = pd.DataFrame({"date": complete_date_range})
    # Format date field to %Y-%m-%d format
    complete_df["date"] = pd.to_datetime(complete_df["date"]).dt.date

    # Merge based on the calendar date part
    if not result_df.empty:
        result_df["date"] = pd.to_datetime(result_df["date"]).dt.date
        complete_df = pd.merge(complete_df, result_df, on="date", how="left")
        complete_df = complete_df.fillna(0)
    else:
        complete_df["nb_tasks"] = 0

    return complete_df[["date", "nb_tasks"]].to_dict(orient="records")


async def get_top_taggers_names_and_count(
    project_id: str,
    filters: ProjectDataFilters,
    limit: int = 3,
    **kwargs,
) -> List[Dict[str, object]]:
    """
    Get the top taggers analytics names and count of a project.
    """
    mongo_db = await get_mongo_db()

    main_filter: Dict[str, object] = {
        "project_id": project_id,
        "removed": {"$ne": True},
        "event_definition.score_range_settings.score_type": "confidence",
    }
    if filters.event_name is not None:
        main_filter["event_name"] = {"$in": filters.event_name}
    # Time range filter
    if filters.created_at_start is not None:
        main_filter["created_at"] = {"$gte": filters.created_at_start}
    if filters.created_at_end is not None:
        main_filter["created_at"] = {
            **main_filter.get("created_at", {}),  # type: ignore
            "$lte": filters.created_at_end,
        }

    # Either the removed filed doesn't exist, either it's not True
    pipeline: List[Dict[str, object]] = [
        {"$match": main_filter},
        {
            "$lookup": {
                "from": "tasks",
                "localField": "task_id",
                "foreignField": "id",
                "as": "tasks",
            }
        },
    ]
    filters.event_name = None
    query_builder = QueryBuilder(
        project_id=project_id, fetch_objects="tasks", filters=filters
    )
    query_builder.pipeline = pipeline
    query_builder.main_doc_filter_tasks(prefix="tasks.")
    await query_builder.task_complex_filters(prefix="tasks.")

    pipeline.extend(
        [
            # Deduplicate the events by task_id and event_name
            {"$unwind": "$tasks"},
            {
                "$group": {
                    "_id": {
                        "task_id": "$task_id",
                        "event_id": "$id",
                        "event_name": "$event_name",
                    }
                }
            },
            {"$group": {"_id": "$_id.event_name", "nb_events": {"$sum": 1}}},
            {"$project": {"_id": 0, "event_name": "$_id", "nb_events": 1}},
            {"$sort": {"nb_events": -1}},
            {"$limit": limit},
        ]
    )
    result = await mongo_db["events"].aggregate(pipeline).to_list(length=limit)

    return result


async def get_tasks_aggregated_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
) -> Dict[str, object]:
    """
    Compute aggregated metrics for the tasks of a project. Used for the Tasks dashboard.
    """
    if await project_has_tasks(project_id) is False:
        return {}

    if filters is None:
        filters = ProjectDataFilters()

    if metrics is None:
        metrics = [
            "total_nb_tasks",
            "global_success_rate",
            "most_detected_event",
            "nb_daily_tasks",
            "events_ranking",
            "success_rate_per_task_position",
            "date_last_clustering_timestamp",
            "last_clustering_composition",
        ]

    today_datetime = datetime.datetime.now(datetime.timezone.utc)
    seven_days_ago_datetime = today_datetime - datetime.timedelta(days=6)
    # Round to the beginning of the day
    seven_days_ago_datetime = seven_days_ago_datetime.replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    output: Dict[str, object] = {}

    if "total_nb_tasks" in metrics:
        output["total_nb_tasks"] = await get_total_nb_of_tasks(
            project_id=project_id, filters=filters
        )
    if "global_success_rate" in metrics:
        output["global_success_rate"] = await get_total_success_rate(
            project_id=project_id, filters=filters
        )
    if "most_detected_event" in metrics:
        output["most_detected_event"] = await get_most_detected_tagger_name(
            project_id=project_id,
            **filters.model_dump(),
        )
    if "nb_daily_tasks" in metrics:
        output["nb_daily_tasks"] = await get_nb_of_daily_tasks(
            project_id=project_id, filters=filters
        )
    if "events_ranking" in metrics:
        output["events_ranking"] = await get_top_taggers_names_and_count(
            project_id=project_id,
            limit=5,
            filters=filters,
        )
    if "daily_success_rate" in metrics:
        output["daily_success_rate"] = await get_daily_success_rate(
            project_id=project_id,
            filters=filters,
        )
    if "success_rate_per_task_position" in metrics:
        output[
            "success_rate_per_task_position"
        ] = await get_success_rate_per_task_position(
            project_id=project_id, filters=filters
        )
    if "date_last_clustering_timestamp" in metrics:
        output[
            "date_last_clustering_timestamp"
        ] = await get_date_last_clustering_timestamp(project_id=project_id)
    if "last_clustering_composition" in metrics:
        output["last_clustering_composition"] = await get_last_clustering_composition(
            project_id=project_id
        )
    return output


async def get_daily_success_rate(
    project_id: str,
    filters: ProjectDataFilters,
    **kwargs,
) -> List[dict]:
    """
    Get the daily success rate of a project.
    """
    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="tasks",
        filters=filters,
    )
    pipeline = await query_builder.build()

    # Add the success rate computation
    pipeline += [
        {"$addFields": {"is_success": {"$eq": ["$flag", "success"]}}},
        {
            "$project": {
                "_id": 0,
                "created_at": 1,
                "is_success": 1,
            }
        },
        {"$sort": {"date": 1}},
    ]
    result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)

    result_df = pd.DataFrame(result)

    start_date_range, end_date_range = extract_date_range(filters)
    if start_date_range is None:
        if not result_df.empty:
            start_date_range = result_df["created_at"].min()
        else:
            start_date_range = datetime.datetime.now()
    if end_date_range is None:
        end_date_range = datetime.datetime.now()

    complete_date_range = pd.date_range(start_date_range, end_date_range, freq="D")
    complete_df = pd.DataFrame({"date": complete_date_range})
    complete_df["date"] = pd.to_datetime(complete_df["date"]).dt.date

    if not result_df.empty:
        result_df["date"] = pd.to_datetime(
            result_df["created_at"], unit="s", utc=True
        ).dt.date
        # Group by date and count
        daily_success_rate = (
            result_df.groupby(["date"])[["is_success"]]
            .mean()
            .reset_index()[["date", "is_success"]]
            .rename(columns={"is_success": "success_rate"})
        )

        # Add missing days
        daily_success_rate = pd.merge(
            complete_df, daily_success_rate, on="date", how="left"
        ).fillna(0)
    else:
        daily_success_rate = complete_df
        daily_success_rate["success_rate"] = 0

    return daily_success_rate[["date", "success_rate"]].to_dict(orient="records")


async def get_total_nb_of_sessions(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
) -> Optional[int]:
    """
    Get the total number of sessions of a project.
    """
    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id, filters=filters, fetch_objects="sessions"
    )
    pipeline = await query_builder.build()
    query_result = (
        await mongo_db["sessions"]
        .aggregate(
            pipeline
            + [
                {"$count": "nb_sessions"},
            ]
        )
        .to_list(length=1)
    )
    if len(query_result) == 0:
        return None

    total_nb_sessions = query_result[0]["nb_sessions"]
    return total_nb_sessions


async def get_nb_tasks_in_sessions(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
    limit: Optional[int] = None,
    sorted: Optional[bool] = False,
) -> Optional[int]:
    """
    Get the total number of tasks in a set of sessions of a project.
    """

    logger.debug(f"Getting the number of tasks in sessions for project {project_id}")
    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="sessions",
        filters=filters,
    )
    pipeline = await query_builder.build()

    if sorted:
        pipeline.append({"$sort": {"created_at": 1}})

    if limit is not None and limit > 0:
        pipeline.append({"$limit": limit})

    pipeline.extend(
        [
            {
                "$lookup": {
                    "from": "tasks",
                    "localField": "id",
                    "foreignField": "session_id",
                    "as": "tasks",
                }
            },
            {"$unwind": "$tasks"},
            {"$count": "nb_tasks"},
        ]
    )

    query_result = await mongo_db["sessions"].aggregate(pipeline).to_list(length=1)

    if len(query_result) == 0:
        return None

    nb_tasks_in_sessions = query_result[0]["nb_tasks"]
    logger.debug(f"Number of tasks in sessions: {nb_tasks_in_sessions}")
    return nb_tasks_in_sessions


async def get_global_average_session_length(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
) -> Optional[float]:
    """
    Get the global average session length of a project.
    """
    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="sessions_with_tasks",
        filters=filters,
    )
    pipeline = await query_builder.build()

    query_result = (
        await mongo_db["sessions"]
        .aggregate(
            pipeline
            + [
                {
                    "$group": {
                        "_id": None,
                        "avg_session_length": {"$avg": "$session_length"},
                    }
                },
                {"$project": {"_id": 0, "avg_session_length": 1}},
            ]
        )
        .to_list(length=1)
    )

    if len(query_result) == 0:
        return None

    global_avg_session_length = query_result[0]["avg_session_length"]
    return global_avg_session_length


async def get_last_message_success_rate(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
) -> Optional[float]:
    """
    Get the success rate of the last message of a project.
    """
    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="sessions",
        filters=filters,
    )
    pipeline = await query_builder.build()

    pipeline.extend(
        [
            {
                "$lookup": {
                    "from": "tasks",
                    "localField": "id",
                    "foreignField": "session_id",
                    "as": "tasks",
                }
            },
            # Sort tasks to make the latest one first
            {
                "$set": {
                    "tasks": {
                        "$sortArray": {
                            "input": "$tasks",
                            "sortBy": {"task_position": -1},
                        },
                    }
                }
            },
            # Get the first task (the one with the greatest task_position)
            {"$set": {"tasks": {"$arrayElemAt": ["$tasks", 0]}}},
            # Add a field "is_success" to the task
            {
                "$set": {
                    "tasks.is_success": {
                        "$cond": [{"$eq": ["$tasks.flag", "success"]}, 1, 0]
                    }
                }
            },
            # Group to calculate success rate
            {
                "$group": {
                    "_id": 0,
                    "count": {"$count": {}},
                    "nb_success": {"$sum": "$tasks.is_success"},
                    "success_rate": {"$avg": "$tasks.is_success"},
                }
            },
            {"$project": {"_id": 0, "success_rate": 1}},
        ]
    )

    result = await mongo_db["sessions"].aggregate(pipeline).to_list(length=1)

    if len(result) == 0:
        return None

    last_message_success_rate = result[0]["success_rate"]
    return last_message_success_rate


async def get_nb_sessions_per_day(
    project_id: str,
    filters: ProjectDataFilters,
) -> List[dict]:
    """
    Get the nb of sessions per day of a project.
    """
    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="sessions",
        filters=filters,
    )
    pipeline = await query_builder.build()
    pipeline.extend(
        [
            # Transform the created_at field to a date
            {
                "$addFields": {
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": {"$toDate": {"$multiply": ["$created_at", 1000]}},
                        }
                    }
                }
            },
            {"$group": {"_id": "$date", "nb_sessions": {"$sum": 1}}},
            {"$project": {"_id": 0, "date": "$_id", "nb_sessions": 1}},
        ]
    )

    result = await mongo_db["sessions"].aggregate(pipeline).to_list(length=None)

    # Add missing days in the date range
    results_df = pd.DataFrame(result)
    start_date_range, end_date_range = extract_date_range(filters)
    if start_date_range is None:
        if not results_df.empty:
            start_date_range = results_df["date"].min()
        else:
            start_date_range = datetime.datetime.now()
    if end_date_range is None:
        end_date_range = datetime.datetime.now()

    complete_date_range = pd.date_range(start_date_range, end_date_range, freq="D")
    complete_df = pd.DataFrame({"date": complete_date_range})
    complete_df["date"] = pd.to_datetime(complete_df["date"]).dt.date

    if not results_df.empty:
        results_df["date"] = pd.to_datetime(results_df["date"]).dt.date
        complete_df = pd.merge(complete_df, results_df, on="date", how="left")
        complete_df = complete_df.fillna(0)
    else:
        complete_df["nb_sessions"] = 0

    return complete_df[["date", "nb_sessions"]].to_dict(orient="records")


async def get_nb_sessions_histogram(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
):
    """
    Get the number of sessions per session length
    """
    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="sessions",
        filters=filters,
    )
    pipeline = await query_builder.build()

    result = (
        await mongo_db["sessions"]
        .aggregate(
            pipeline
            + [
                {
                    "$lookup": {
                        "from": "tasks",
                        "localField": "id",
                        "foreignField": "session_id",
                        "as": "tasks",
                    }
                },
                {"$addFields": {"session_length": {"$size": "$tasks"}}},
                {
                    "$group": {
                        "_id": "$session_length",
                        "nb_sessions": {"$sum": 1},
                    }
                },
                {"$project": {"_id": 0, "session_length": "$_id", "nb_sessions": 1}},
                {"$sort": {"session_length": 1}},
            ]
        )
        .to_list(length=None)
    )

    df = pd.DataFrame(result)
    if df.empty:
        return []
    else:
        # Add missing session lengths
        complete_session_lengths = pd.DataFrame(
            {"session_length": range(1, df["session_length"].max() + 1)}
        )
        df = pd.merge(
            complete_session_lengths,
            df,
            on="session_length",
            how="left",
            validate="m:1",
        ).fillna(0)
        return df[["session_length", "nb_sessions"]].to_dict(orient="records")


async def get_sessions_aggregated_metrics(
    project_id: str,
    quantile_filter: Optional[float] = None,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
    limit: Optional[int] = None,
) -> Dict[str, object]:
    """
    Compute aggregated metrics for the sessions of a project. Used for the Sessions dashboard.
    """

    if await project_has_sessions(project_id) is False:
        return {}

    if filters is None:
        filters = ProjectDataFilters()

    if metrics is None:
        metrics = [
            "total_nb_sessions",
            "average_session_length",
            "last_task_success_rate",
            "nb_sessions_per_day",
            "session_length_histogram",
            "success_rate_per_task_position",
            "nb_tasks_in_sessions",
        ]

    today_datetime = datetime.datetime.now(datetime.timezone.utc)
    seven_days_ago_datetime = today_datetime - datetime.timedelta(days=6)
    # Round to the beginning of the day
    seven_days_ago_datetime = seven_days_ago_datetime.replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    output: Dict[str, object] = {}

    if "total_nb_sessions" in metrics:
        output["total_nb_sessions"] = await get_total_nb_of_sessions(
            project_id=project_id,
            filters=filters,
        )
    if "average_session_length" in metrics:
        output["average_session_length"] = await get_global_average_session_length(
            project_id=project_id,
            filters=filters,
        )
    if "last_task_success_rate" in metrics:
        output["last_task_success_rate"] = await get_last_message_success_rate(
            project_id=project_id,
            filters=filters,
        )
    if "nb_sessions_per_day" in metrics:
        output["nb_sessions_per_day"] = await get_nb_sessions_per_day(
            project_id=project_id, filters=filters
        )
    if "session_length_histogram" in metrics:
        output["session_length_histogram"] = await get_nb_sessions_histogram(
            project_id=project_id,
            filters=filters,
        )
    if "success_rate_per_task_position" in metrics:
        output[
            "success_rate_per_task_position"
        ] = await get_success_rate_per_task_position(
            project_id=project_id, quantile_filter=quantile_filter, filters=filters
        )
    if "nb_tasks_in_sessions" in metrics:
        output["nb_tasks_in_sessions"] = await get_nb_tasks_in_sessions(
            project_id=project_id,
            filters=filters,
            limit=limit,
        )
    return output


async def create_ab_tests_table(project_id: str, limit: int = 1000) -> List[ABTest]:
    """
    Compute the AB tests of a project. Used for the AB Tests dashboard.
    """
    # Create an aggregated table
    mongo_db = await get_mongo_db()

    ab_tests = (
        await mongo_db["tasks"]
        .aggregate(
            [
                {
                    "$match": {
                        "project_id": project_id,
                        "test_id": None,
                    }
                },
                {
                    "$addFields": {
                        "version_id": {
                            "$cond": [
                                {
                                    "$or": [
                                        {"$eq": ["$metadata", None]},
                                        {"$eq": ["$metadata.version_id", None]},
                                    ]
                                },
                                "None",
                                "$metadata.version_id",
                            ]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$version_id",
                        "score": {
                            "$avg": {"$cond": [{"$eq": ["$flag", "success"]}, 1, 0]}
                        },
                        "nb_tasks": {"$sum": 1},
                        "first_task_ts": {"$min": "$created_at"},
                        "last_task_ts": {"$max": "$created_at"},
                        # "score_std": {
                        #     "$stdDevSamp": {
                        #         "$cond": [{"$eq": ["$flag", "success"]}, 1, 0]
                        #     }
                        # },
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "version_id": "$_id",
                        "score": 1,
                        "nb_tasks": 1,
                        "score_std": 1,
                        "first_task_ts": 1,
                        "last_task_ts": 1,
                    }
                },
                {"$sort": {"first_task_ts": -1}},
            ]
        )
        .to_list(length=limit)
    )
    logger.info(f"AB tests: {ab_tests}")
    # Validate models
    valid_ab_tests = []
    for ab_test in ab_tests:
        try:
            valid_ab_test = ABTest.model_validate(ab_test)
            valid_ab_tests.append(valid_ab_test)
        except pydantic.ValidationError:
            logger.debug(f"Skipping invalid ab_test: {ab_test}")

    # Compute the standard deviation and the 95% confidence interval
    for ab_test in valid_ab_tests:
        ab_test.score_std = math.sqrt(ab_test.score * (1 - ab_test.score))
        if ab_test.nb_tasks > 0:
            ab_test.confidence_interval = [
                max(
                    ab_test.score
                    - 1.96 * ab_test.score_std / math.sqrt(ab_test.nb_tasks),
                    0,
                ),
                min(
                    ab_test.score
                    + 1.96 * ab_test.score_std / math.sqrt(ab_test.nb_tasks),
                    1,
                ),
            ]

    return valid_ab_tests


async def get_success_rate_by_event_name(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
) -> Dict[str, float]:
    """
    Get the success rate by event name of a project.
    """
    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {
        "project_id": project_id,
        "removed": {"$ne": True},
    }
    if not filters:
        filters = ProjectDataFilters()

    if filters.created_at_start is not None:
        main_filter["created_at"] = {"$gte": filters.created_at_start}
    if filters.created_at_end is not None:
        main_filter["created_at"] = {
            **main_filter.get("created_at", {}),  # type: ignore
            "$lte": filters.created_at_end,
        }

    pipeline: List[Dict[str, object]] = [
        {"$match": main_filter},
        {
            "$lookup": {
                "from": "tasks",
                "localField": "task_id",
                "foreignField": "id",
                "as": "tasks",
            }
        },
        {"$unwind": "$tasks"},
    ]

    query_builder = QueryBuilder(
        project_id=project_id, fetch_objects="tasks", filters=filters
    )
    query_builder.pipeline = pipeline
    query_builder.main_doc_filter_tasks(prefix="tasks.")
    await query_builder.task_complex_filters(prefix="tasks.")

    pipeline = [
        # Deduplicate based on event.event_name x task.id
        {
            "$group": {
                "_id": {
                    "event_name": "$event_name",
                    "task_id": "$tasks.id",
                },
                "flag": {"$first": "$tasks.flag"},
            }
        },
        {
            "$group": {
                "_id": "$_id.event_name",
                "success_rate": {
                    "$avg": {"$cond": [{"$eq": ["$flag", "success"]}, 1, 0]}
                },
            }
        },
        {"$project": {"event_name": "$_id", "success_rate": 1, "_id": 0}},
        {"$sort": {"success_rate": -1}},
    ]
    result = await mongo_db["events"].aggregate(pipeline).to_list(length=None)
    return result


async def get_total_nb_of_detections(
    project_id: str,
    filters: ProjectDataFilters,
    **kwargs,
) -> int:
    """
    Get the total number of detections of a project. Uses the
    job_results collection.
    """
    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {"project_id": project_id}
    # Time range filter
    if filters.created_at_start is not None:
        main_filter["created_at"] = {"$gte": filters.created_at_start}
    if filters.created_at_end is not None:
        main_filter["created_at"] = {"$lte": filters.created_at_end}
    if filters.event_id is not None:
        main_filter["job_metadata.id"] = {"$in": filters.event_id}
    pipeline: List[Dict[str, object]] = [
        {"$match": main_filter},
        {"$count": "nb_detections"},
    ]
    query_result = await mongo_db["job_results"].aggregate(pipeline).to_list(length=1)
    if query_result is not None and len(query_result) > 0:
        total_nb_detections = query_result[0]["nb_detections"]
    else:
        total_nb_detections = 0
    return total_nb_detections


async def get_y_pred_y_true(
    project_id: str,
    filters: ProjectDataFilters,
    **kwargs,
) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
    """
    Get the y_pred for an event.
    """
    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {"project_id": project_id}
    # Time range filter
    if filters.created_at_start is not None:
        main_filter["created_at"] = {"$gte": filters.created_at_start}
    if filters.created_at_end is not None:
        main_filter["created_at"] = {"$lte": filters.created_at_end}

    main_filter["event_definition.id"] = {"$in": filters.event_id}

    query_result = (
        await mongo_db["events"]
        .find(main_filter)
        .sort("created_at", -1)
        .to_list(
            # Hardcoded limit to avoid memory issues
            # TODO : Perform all the filtering in the query (or multiple)
            # to avoid this limit
            length=5_000,
        )
    )
    if query_result is None or len(query_result) == 0:
        logger.info("No events found")
        return None, None

    first_event = Event.model_validate(query_result[0])
    logger.debug(f"First event: {first_event.event_name}")
    if (
        first_event.event_definition is None
        or first_event.event_definition.score_range_settings is None
    ):
        logger.info("No score range settings found")
        return None, None
    event_type = first_event.event_definition.score_range_settings.score_type
    logger.debug(f"Event type: {event_type}")

    # Convert to DataFrame
    df = pd.DataFrame(query_result)

    # Fill empty values
    df["removed"] = df["removed"].astype(bool).fillna(False)
    df["confirmed"] = df["confirmed"].astype(bool).fillna(False)
    df = df.dropna(subset=["score_range"])

    if event_type == "confidence":
        mask_y_pred_true = (
            ((df["source"] != "owner") & (df["confirmed"]) & (~df["removed"]))
            | ((df["source"] != "owner") & (df["confirmed"]) & (~df["removed"]))
            | ((df["source"] != "owner") & (~df["confirmed"]) & (df["removed"]))
        )

        mask_y_pred_false = (
            ((df["source"] == "owner") & (~df["confirmed"]) & (~df["removed"]))
            | ((df["source"] == "owner") & (df["confirmed"]) & (~df["removed"]))
            | ((df["source"] == "owner") & (df["confirmed"]) & (df["removed"]))
        )

        mask_y_true_true = (
            (df["source"] != "owner") & (df["confirmed"]) & (~df["removed"])
        ) | ((df["source"] == "owner") & (df["confirmed"]) & (~df["removed"]))
        # Apply the masks to get the desired DataFrames
        df = pd.concat([df[mask_y_pred_true], df[mask_y_pred_false]], ignore_index=True)
        df["y_pred"] = mask_y_pred_true
        df["y_true"] = mask_y_true_true

    elif event_type == "category":
        mask = (
            ((df["source"] != "owner") & (df["confirmed"]) & (~df["removed"]))
            | ((df["source"] != "owner") & (df["confirmed"]) & (~df["removed"]))
            | ((df["source"] != "owner") & (~df["confirmed"]) & (df["removed"]))
            | ((df["source"] == "owner") & (~df["confirmed"]) & (~df["removed"]))
            | ((df["source"] == "owner") & (df["confirmed"]) & (~df["removed"]))
            | ((df["source"] == "owner") & (df["confirmed"]) & (df["removed"]))
        )
        df = df[mask]

        df["y_pred"] = df["score_range"].apply(lambda x: x.get("label"))
        df["y_true"] = None

        df.loc[
            ((df["source"] != "owner") & (df["confirmed"]) & (~df["removed"])),
            "y_true",
        ] = df.loc[
            ((df["source"] != "owner") & (df["confirmed"]) & (~df["removed"])),
            "score_range",
        ].apply(lambda x: x.get("corrected_label"))

        df.loc[
            ((df["source"] != "owner") & (df["confirmed"]) & (~df["removed"])),
            "y_true",
        ] = df.loc[
            ((df["source"] != "owner") & (df["confirmed"]) & (~df["removed"])),
            "score_range",
        ].apply(lambda x: x.get("corrected_label"))

        df.loc[
            ((df["source"] == "owner") & (df["confirmed"]) & (~df["removed"])),
            "y_true",
        ] = df.loc[
            ((df["source"] == "owner") & (df["confirmed"]) & (~df["removed"])),
            "score_range",
        ].apply(lambda x: x.get("label"))

    elif event_type == "range":
        mask = (
            (df["source"] == "owner") & (~df["removed"]) & (df["score_range"].notna())
        ) | ((df["source"] != "owner") & (df["confirmed"]) & (~df["removed"]))

        df = df[mask]

        df["y_pred"] = df["score_range"].apply(lambda x: x.get("value"))
        df["y_true"] = df["score_range"].apply(lambda x: x.get("corrected_value"))

        # I fill the y_true with the value if the corrected_value is None
        df["y_true"] = df["y_true"].fillna(df["y_pred"])
    else:
        raise NotImplementedError(
            f"Event type {event_type} is not implemented for y_pred and y_true"
        )

    if not df.empty:
        y_pred = df["y_pred"].fillna("None")
        y_true = df["y_true"].fillna("None")
    else:
        y_pred = None
        y_true = None
    return y_pred, y_true


async def get_category_distribution(
    project_id: str,
    filters: ProjectDataFilters,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Filter the events to keep only the ones that are category events.

    Find the distribution of the categories.
    """
    db = await get_mongo_db()

    main_filter: Dict[str, object] = {
        "project_id": project_id,
        "removed": {"$ne": True},
        # "event_definition.event_name": {"$in": filters.event_name},
        # "event_definition.id": {"$in": filters.event_id},
    }
    if filters.event_id is not None:
        main_filter["event_definition.id"] = {"$in": filters.event_id}
    if filters.event_name is not None:
        main_filter["event_definition.event_name"] = {"$in": filters.event_name}
    # Time range filter
    if filters.created_at_start is not None:
        main_filter["created_at"] = {"$gte": filters.created_at_start}
    if filters.created_at_end is not None:
        main_filter["created_at"] = {"$lte": filters.created_at_end}

    # Filter by event type
    main_filter["event_definition.score_range_settings.score_type"] = "category"

    pipeline = [
        {"$match": main_filter},
        {
            "$group": {
                "_id": {
                    # Group by event name and category
                    "event_name": "$event_definition.event_name",
                    "category": "$score_range.label",
                },
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "category": "$_id.category",
                "count": 1,
                "event_name": "$_id.event_name",
            }
        },
    ]

    result = await db["events"].aggregate(pipeline).to_list(length=None)
    if result is None or len(result) == 0:
        logger.debug("Event category distribution is empty")
        return {}

    # Format the results : {event_name: [{category, count}]}
    output: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in result:
        event_name = item["event_name"]
        category = item["category"]
        count = item["count"]
        output[event_name].append({"category": category, "count": count})

    return output


async def get_events_aggregated_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
) -> Dict[str, object]:
    if filters is None:
        filters = ProjectDataFilters()
    if metrics is None:
        metrics = [
            "success_rate_by_event_name",
        ]
    output: Dict[str, object] = {}
    if "success_rate_by_event_name" in metrics:
        output["success_rate_by_event_name"] = await get_success_rate_by_event_name(
            project_id=project_id, filters=filters
        )
    if "total_nb_events" in metrics:
        output["total_nb_events"] = await get_total_nb_of_detections(
            project_id=project_id, filters=filters
        )
    if "category_distribution" in metrics:
        logger.info("Getting category distribution")
        output["category_distribution"] = await get_category_distribution(
            project_id=project_id, filters=filters
        )

    # Some metrics require y_pred and y_true
    performance_metrics = [
        "mean_squared_error",
        "r_squared",
        "f1_score_binary",
        "precision_binary",
        "recall_binary",
        "f1_score_multiclass",
        "precision_multiclass",
        "recall_multiclass",
    ]
    intersection_metrics = list(set(metrics).intersection(set(performance_metrics)))
    if filters.event_id is not None and len(intersection_metrics) > 0:
        y_pred, y_true = await get_y_pred_y_true(
            project_id=project_id,
            filters=filters,
        )
        if y_pred is not None and y_true is not None:
            if "mean_squared_error" in metrics:
                output["mean_squared_error"] = float(
                    root_mean_squared_error(y_true, y_pred)
                )
            if "r_squared" in metrics:
                output["r_squared"] = float(r2_score(y_true, y_pred))
            if "f1_score_binary" in metrics:
                output["f1_score_binary"] = float(f1_score(y_true, y_pred))
            if "precision_binary" in metrics:
                output["precision_binary"] = float(precision_score(y_true, y_pred))
            if "recall_binary" in metrics:
                output["recall_binary"] = float(recall_score(y_true, y_pred))
            if "f1_score_multiclass" in metrics:
                output["f1_score_multiclass"] = float(
                    f1_score(y_true, y_pred, average="weighted")
                )
            if "precision_multiclass" in metrics:
                output["precision_multiclass"] = float(
                    precision_score(y_true, y_pred, average="weighted")
                )
            if "recall_multiclass" in metrics:
                output["recall_multiclass"] = float(
                    recall_score(y_true, y_pred, average="weighted")
                )
        else:
            logger.info(f"No y_pred and y_true found for event {filters.event_id}")
    elif filters.event_id is None and len(intersection_metrics) > 0:
        logger.error(
            f"Event ID is required to compute performance metrics: {intersection_metrics}"
        )

    logger.debug(output)
    return output


async def graph_number_of_daily_tasks(project_id: str):
    """
    Graph the number of daily tasks for last week of a project.

    Group tasks in 4 categories: success, failure, undefined, and total.
    """
    mongo_db = await get_mongo_db()
    seven_days_ago_timestamp, today_timestamp = get_last_week_timestamps()

    # Aggregation pipeline
    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                "created_at": {
                    "$gte": seven_days_ago_timestamp,
                    "$lte": today_timestamp,
                },
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": {"$toDate": {"$multiply": ["$created_at", 1000]}},
                    }
                },
                "success": {"$sum": {"$cond": [{"$eq": ["$flag", "success"]}, 1, 0]}},
                "failure": {"$sum": {"$cond": [{"$eq": ["$flag", "failure"]}, 1, 0]}},
                "total": {"$sum": 1},
            }
        },
        {
            "$addFields": {
                "undefined": {
                    "$subtract": ["$total", {"$add": ["$success", "$failure"]}]
                },
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "_id": 0,
                "date": "$_id",
                "success": 1,
                "failure": 1,
                "undefined": 1,
            }
        },
    ]
    # Query Mongo
    result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)
    result_df = pd.DataFrame(result)
    # Add missing days to the result, and set the missing values to 0
    complete_date_range = pd.date_range(
        datetime.datetime.fromtimestamp(
            seven_days_ago_timestamp, datetime.timezone.utc
        ),
        datetime.datetime.fromtimestamp(today_timestamp, datetime.timezone.utc),
        freq="D",
    )
    complete_df = pd.DataFrame({"date": complete_date_range})
    complete_df["date"] = pd.to_datetime(complete_df["date"]).dt.date

    if not result_df.empty:
        result_df["date"] = pd.to_datetime(result_df["date"]).dt.date
        result_df = pd.merge(complete_df, result_df, on="date", how="left").fillna(0)
    else:
        result_df = complete_df
        result_df["success"] = 0
        result_df["failure"] = 0
        result_df["undefined"] = 0

    return result_df.to_dict(orient="records")


async def get_events_per_day(project_id: str):
    """
    Get the number of events per day for the last week of a project.

    Resut should be like this:
    {
        "unique_event_names": ["event_name_1", "event_name_2", ...],
        "date": [date1, date2, ...],
        "event_name_1": [count1, count2, ...],
        "event_name_2": [count1, count2, ...],
        ...
        "total": [count1, count2, ...],
    }
    """
    mongo_db = await get_mongo_db()
    seven_days_ago_timestamp, today_timestamp = get_last_week_timestamps()

    pipeline = [
        # Filter tasks of the last week
        {
            "$match": {
                "project_id": project_id,
                "created_at": {
                    "$gte": seven_days_ago_timestamp,
                    "$lte": today_timestamp,
                },
                "removed": {"$ne": True},
            }
        },
        {
            "$addFields": {
                "date": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": {"$toDate": {"$multiply": ["$created_at", 1000]}},
                    },
                }
            },
        },
        {"$unwind": "$events"},
        # Deduplicate based on event.event_name x task.id
        {
            "$group": {
                "_id": {
                    "date": "$date",
                    "event_name": "$events.event_name",
                    "task_id": "$id",
                },
            }
        },
        # Group by event name and date to get the number of events per day
        {
            "$group": {
                "_id": {
                    "date": "$_id.date",
                    "event_name": "$_id.event_name",
                },
                "count": {"$sum": 1},
            }
        },
        # Project the result
        {
            "$project": {
                "_id": 0,
                "date": "$_id.date",
                "event_name": "$_id.event_name",
                "count": 1,
            }
        },
    ]
    result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)
    result = pd.DataFrame(result)

    # Get the list of event names
    if "event_name" in result.columns:
        unique_event_names = result["event_name"].unique().tolist()
    else:
        unique_event_names = []

    if not result.empty:
        # Unpivot the dataframe to get the result in the expected format
        result = result.pivot(
            index="date", columns="event_name", values="count"
        ).reset_index()
        result = result.fillna(0)
        # Create a total column, sum of all columns in unique_event_names
        result["total"] = result[unique_event_names].sum(axis=1)

    # Add missing days to the result, and set the missing values to 0
    complete_date_range = pd.date_range(
        datetime.datetime.fromtimestamp(
            seven_days_ago_timestamp, datetime.timezone.utc
        ),
        datetime.datetime.fromtimestamp(today_timestamp, datetime.timezone.utc),
        freq="D",
    )
    complete_df = pd.DataFrame({"date": complete_date_range})
    complete_df["date"] = pd.to_datetime(complete_df["date"]).dt.date

    if not result.empty:
        result["date"] = pd.to_datetime(result["date"]).dt.date
        result = pd.merge(complete_df, result, on="date", how="left").fillna(0)
    else:
        result = complete_df
        result["total"] = 0

    # Format the result
    output = {}
    output["data"] = result.to_dict(orient="records")
    output["unique_event_names"] = unique_event_names

    return output


async def get_dashboard_aggregated_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
):
    if metrics is None:
        metrics = [
            "number_of_daily_tasks",
        ]
    output: Dict[str, object] = {}
    if "number_of_daily_tasks" in metrics:
        output["number_of_daily_tasks"] = await graph_number_of_daily_tasks(
            project_id=project_id,
        )
    if "events_per_day" in metrics:
        output["events_per_day"] = await get_events_per_day(project_id=project_id)

    return output


async def get_ab_tests_versions(
    project_id: str,
    versionA: Optional[str],
    versionB: Optional[str],
    selected_events_ids: Optional[List[str]] = None,
    filtersA: Optional[ProjectDataFilters] = None,
    filtersB: Optional[ProjectDataFilters] = None,
) -> List[Dict[str, Union[str, float, int]]]:
    """
    - For boolean events, gets the number of times the event was detected in each task with the two versions of the model.
    - For categorical events, gets the number of times each category was detected in each task with the two versions of the model.
    - For range evnts, shows the average value of the score for each task with the two versions of the model.
    """
    mongo_db = await get_mongo_db()
    collection_name = "events"

    logger.debug(f"versionA: {versionA}, versionB: {versionB}")
    logger.debug(f"filtersA: {filtersA}, filtersB: {filtersB}")
    if versionA == "None":
        versionA = None
    if versionB == "None":
        versionB = None

    pipeline_A = await get_number_of_events_version(
        project_id=project_id,
        version=versionA,
        filters=filtersA,
        selected_events_ids=selected_events_ids,
    )

    results_A = (
        await mongo_db[collection_name].aggregate(pipeline_A).to_list(length=None)
    )

    if not results_A or len(results_A) == 0:
        logger.info("No results found for version A")

    pipeline_B = await get_number_of_events_version(
        project_id=project_id,
        version=versionB,
        filters=filtersB,
        selected_events_ids=selected_events_ids,
    )
    results_B = (
        await mongo_db[collection_name].aggregate(pipeline_B).to_list(length=None)
    )
    if not results_B or len(results_B) == 0:
        logger.info("No results found for version B")
        if not results_A or len(results_A) == 0:
            return []

    results = results_A + results_B

    logger.debug(f"Results: {results}")

    # This dict will have event_names as keys, and the values will be dictionnaries with the version_id as keys and the count as values
    total_tasks_with_A = await get_nb_tasks_version(
        version=versionA,
        project_id=project_id,
        filters=filtersA,
    )
    logger.info(f"Total tasks with version A: {total_tasks_with_A}")

    total_tasks_with_B = await get_nb_tasks_version(
        version=versionB,
        project_id=project_id,
        filters=filtersB,
    )

    logger.info(f"Total tasks with version B: {total_tasks_with_B}")

    if total_tasks_with_B == 0 and total_tasks_with_A == 0:
        return []

    graph_values = {}
    graph_values_range = {}
    events_to_normalize = []
    for result in results:
        if "event_name" not in result:
            continue
        if (
            "event_type" not in result or result["event_type"] == "confidence"
        ):  # We sum up the count for each version
            event_name = result["event_name"]
            for event_result in result["results"]:
                if "version_id" not in event_result:
                    continue
                if event_name not in graph_values:
                    graph_values[event_name] = {
                        event_result["version_id"]: event_result["count"]
                    }
                else:
                    if event_result["version_id"] not in graph_values[event_name]:
                        graph_values[event_name][event_result["version_id"]] = (
                            event_result["count"]
                        )
                    else:
                        graph_values[event_name][event_result["version_id"]] += (
                            event_result["count"]
                        )

            # We normalize the count by the total number of tasks with each version to get the percentage
            if versionA in graph_values.get(event_name, []):
                graph_values[event_name][versionA] = graph_values[event_name][versionA]
            if versionB in graph_values.get(event_name, []):
                graph_values[event_name][versionB] = graph_values[event_name][versionB]

        elif (
            result["event_type"] == "category"
        ):  # We sum up up the count for each label for each version
            for event_result in result["results"]:
                if "version_id" not in event_result:
                    continue
                event_name = result["event_name"] + "- " + event_result["event_label"]
                if event_name not in graph_values:
                    graph_values[event_name] = {
                        event_result["version_id"]: event_result["count"]
                    }
                else:
                    if event_result["version_id"] not in graph_values[event_name]:
                        graph_values[event_name][event_result["version_id"]] = (
                            event_result["count"]
                        )
                    else:
                        graph_values[event_name][event_result["version_id"]] += (
                            event_result["count"]
                        )
                # We normalize the count by the total number of tasks with each version
                if event_result["version_id"] == versionA:
                    graph_values[event_name][versionA] = graph_values[event_name][
                        versionA
                    ]
                if event_result["version_id"] == versionB:
                    graph_values[event_name][versionB] = graph_values[event_name][
                        versionB
                    ]

        elif result["event_type"] == "range":  # We average the score for each version
            divide_for_correct_average = {}
            event_name = result["event_name"]
            for event_result in result["results"]:
                if "version_id" not in event_result:
                    continue
                if event_name not in graph_values_range:
                    graph_values_range[event_name] = {
                        event_result["version_id"]: event_result["score"]
                        * event_result["count"]
                    }
                else:
                    if event_result["version_id"] not in graph_values_range[event_name]:
                        graph_values_range[event_name][event_result["version_id"]] = (
                            event_result["score"] * event_result["count"]
                        )
                    else:
                        graph_values_range[event_name][event_result["version_id"]] += (
                            event_result["score"] * event_result["count"]
                        )

                if event_result["version_id"] not in divide_for_correct_average:
                    divide_for_correct_average[event_result["version_id"]] = (
                        event_result["count"]
                    )
                else:
                    divide_for_correct_average[event_result["version_id"]] += (
                        event_result["count"]
                    )

            for version in divide_for_correct_average:
                graph_values_range[event_name][version] = (
                    graph_values_range[event_name][version]
                    / divide_for_correct_average[version]
                )

            events_to_normalize.append(event_name)

        else:
            logger.error(f"New event type is not handled: {result['event_type']}")

    if versionA is None:
        versionA = "None"
    if versionB is None:
        versionB = "None"

    formatted_graph_values = []
    for event_name, values in graph_values.items():
        formatted_graph_values.append(
            {
                "event_name": event_name,
                versionA: values.get(versionA, 0) / total_tasks_with_A
                if total_tasks_with_A != 0
                else 0,
                versionB: values.get(versionB, 0) / total_tasks_with_B
                if total_tasks_with_B != 0
                else 0,
                versionA + "_tooltip": values.get(versionA, 0),
                versionB + "_tooltip": values.get(versionB, 0),
            }
        )
    for event_name, values in graph_values_range.items():
        formatted_graph_values.append(
            {
                "event_name": event_name,
                versionA: values.get(versionA, 0) / 5,
                versionB: values.get(versionB, 0) / 5,
                versionA + "_tooltip": values.get(versionA, 0),
                versionB + "_tooltip": values.get(versionB, 0),
            }
        )

    # We sort to keep the order the same
    formatted_graph_values = sorted(
        formatted_graph_values, key=lambda x: x["event_name"]
    )

    return formatted_graph_values


async def get_nb_tasks_version(
    project_id: str,
    version: Optional[str] = None,
    filters: Optional[ProjectDataFilters] = None,
) -> int:
    """
    Get the number of tasks with the version_id in the filters.
    """
    mongo_db = await get_mongo_db()

    if filters is not None and (
        filters.created_at_start is not None or filters.created_at_end is not None
    ):
        pipeline = [
            {
                "$match": {
                    "project_id": project_id,
                },
            }
        ]
        if filters.created_at_start is not None:
            if isinstance(filters.created_at_start, datetime.datetime):
                filters.created_at_start = int(filters.created_at_start.timestamp())
            pipeline.append(
                {
                    "$match": {
                        "created_at": {"$gte": filters.created_at_start},  # type: ignore
                    }
                }
            )
        if filters.created_at_end is not None:
            if isinstance(filters.created_at_end, datetime.datetime):
                filters.created_at_end = int(filters.created_at_end.timestamp())
            pipeline.append(
                {
                    "$match": {
                        "created_at": {"$lte": filters.created_at_end},  # type: ignore
                    }
                }
            )
        pipeline.append(
            {
                "$count": "count",  # type: ignore
            }
        )
    else:
        pipeline = [
            {
                "$match": {
                    "project_id": project_id,
                    "metadata.version_id": version,  # type: ignore
                }
            },
            {
                "$count": "count",  # type: ignore
            },
        ]

    result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)

    if not result or len(result) == 0:
        return 0

    return result[0]["count"]


async def get_number_of_events_version(
    project_id: str,
    version: Optional[str] = None,
    filters: Optional[ProjectDataFilters] = None,
    selected_events_ids: Optional[List[str]] = None,
) -> List:
    if filters is None:
        filters = ProjectDataFilters()

    main_filter = {
        "project_id": project_id,
        "removed": {"$ne": ["$events.removed", True]},
    }
    # Apply the event_id filter early to reduce the number of events to process
    if filters.event_id is not None:
        main_filter["event_definition.id"] = {"$in": filters.event_id}

    pipeline = [
        {"$match": main_filter},
        {
            "$lookup": {
                "from": "tasks",
                "localField": "task_id",
                "foreignField": "id",
                "as": "task",
            }
        },
        {"$unwind": "$task"},
        # We look up the last version of the event_definition to have the information up to date
        {
            "$lookup": {
                "from": "event_definitions",
                "localField": "event_definition.id",
                "foreignField": "id",
                "as": "event_def",
            }
        },
        {"$unwind": "$event_def"},
    ]

    # I want to set the version_id of all task to versionA if the version_id is None and the task was created in the filterA
    # Check if the filters are not None or empty
    if filters.created_at_start is not None or filters.created_at_end is not None:
        filtering = []
        if filters.created_at_start is not None:
            if isinstance(filters.created_at_start, datetime.datetime):
                filters.created_at_start = int(filters.created_at_start.timestamp())
            filtering.append({"$gte": ["$task.created_at", filters.created_at_start]})
        if filters.created_at_end is not None:
            if isinstance(filters.created_at_end, datetime.datetime):
                filters.created_at_end = int(filters.created_at_end.timestamp())
            filtering.append({"$lte": ["$task.created_at", filters.created_at_end]})
        pipeline.append(
            {
                "$set": {
                    "task.metadata.version_id": {
                        "$cond": [
                            {
                                "$and": filtering,
                            },
                            version,
                            "$task.metadata.version_id",
                        ]
                    }
                }
            },
        )

    pipeline.extend(
        [
            {
                "$match": {
                    "task.metadata.version_id": {"$in": [version]},
                }
            },
            {
                "$group": {
                    "_id": {
                        "version_id": "$task.metadata.version_id",
                        "event_definition_id": "$event_def.id",
                        "event_label": "$score_range.label",
                        "event_name": "$event_def.event_name",
                        "event_type": "$event_def.score_range_settings.score_type",
                    },
                    "count": {"$sum": 1},
                    "score": {"$avg": "$score_range.value"},
                },
            },
        ]
    )

    # Keep only the events that are in the selected_events_id list
    if selected_events_ids is not None:
        pipeline.append(
            {
                "$match": {
                    "_id.event_definition_id": {"$in": selected_events_ids},
                },
            }
        )

    pipeline.extend(
        [
            # For range type events, we need to average the score
            # For confidence type events, we need to count the number of times the event was detected
            # For categorical events, we need to count the number of times each label was detected$
            {
                "$project": {
                    "_id": 0,
                    "version_id": "$_id.version_id",
                    "event_name": "$_id.event_name",
                    "event_label": "$_id.event_label",
                    "event_type": "$_id.event_type",
                    "count": 1,
                    "score": 1,
                },
            },
            # TODO : Remove this code and implement it in python instead
            # For event_type == "category", concat by event_name and the label then group by event_name
            # For event_type == "range", concat by event_name and average the score
            # For event_type == "confidence", concat by event_name and count the number of times the event was detected
            {
                "$group": {
                    "_id": {
                        "event_definition_id": "$_id.event_definition_id",
                        "event_type": "$event_type",
                        "event_name": "$event_name",
                    },
                    "results": {
                        "$push": {
                            "version_id": "$version_id",
                            "event_label": "$event_label",
                            "count": "$count",
                            "score": "$score",
                        },
                    },
                },
            },
            {
                "$project": {
                    "_id": 0,
                    "event_type": "$_id.event_type",
                    "event_name": "$_id.event_name",
                    "results": 1,
                },
            },
        ]
    )

    return pipeline

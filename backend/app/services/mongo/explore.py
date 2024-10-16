"""
Explore metrics service
"""

import datetime
import math
from collections import defaultdict
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from app.services.mongo.query_builder import QueryBuilder
import pandas as pd
import pydantic

from app.api.platform.models import ABTest, Pagination, ProjectDataFilters
from app.api.platform.models.explore import ClusteringEmbeddingCloud
from app.db.models import Eval, FlattenedTask
from app.db.mongo import get_mongo_db
from app.services.mongo.events import get_all_events
from app.services.mongo.tasks import (
    get_all_tasks,
    get_total_nb_of_tasks,
)
from app.utils import generate_timestamp, get_last_week_timestamps
from fastapi import HTTPException
from loguru import logger
from pymongo import InsertOne, UpdateOne
from sklearn.metrics import (
    f1_score,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)

from phospho.models import Cluster, Clustering, Event


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
    return df_dict


async def get_success_rate_per_task_position(
    project_id,
    filters: ProjectDataFilters,
    quantile_filter: Optional[float] = None,
    **kwargs,
) -> Optional[Dict[str, object]]:
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
    return success_rate_per_message_position_dict


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
    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="tasks",
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

    result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)
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


async def get_date_last_clustering_timestamp(
    project_id: str,
) -> Optional[int]:
    """
    Get the timestamp date of the last clustering for a given project.
    """
    mongo_db = await get_mongo_db()

    result = (
        await mongo_db["private-clusterings"]
        .find({"project_id": project_id})
        .sort([("created_at", -1)])
        .limit(1)
        .to_list(length=1)
    )
    if len(result) == 0:
        return None
    date_last_clustering_timestamp = result[0]["created_at"]
    return date_last_clustering_timestamp


async def get_last_clustering_composition(
    project_id: str,
) -> Optional[List[Dict[str, object]]]:
    """
    Get the composition of the last clustering for a given project.
    """
    mongo_db = await get_mongo_db()

    clustering = (
        await mongo_db["private-clusterings"]
        .find({"project_id": project_id, "status": "completed"})
        .sort([("created_at", -1)])
        .limit(1)
        .to_list(length=1)
    )
    if len(clustering) == 0:
        return None

    clusters = (
        await mongo_db["private-clusters"]
        .find(
            {"clustering_id": clustering[0]["id"]},
            {"name": 1, "description": 1, "size": 1},
        )
        .to_list(length=None)
    )
    clusters = [
        {"name": c["name"], "description": c["description"], "size": c["size"]}
        for c in clusters
    ]
    return clusters


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


async def fetch_all_clusterings(
    project_id: str,
    limit: int = 100,
    with_cluster_names: bool = True,
) -> List[Clustering]:
    """
    Fetch all the clusterings of a project. The clusterings are sorted by creation date.

    Each clustering contains clusters.
    """
    mongo_db = await get_mongo_db()

    pipeline: List[Dict[str, object]] = [
        {"$match": {"project_id": project_id}},
    ]
    if with_cluster_names:
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "private-clusters",
                        "localField": "id",
                        "foreignField": "clustering_id",
                        "as": "clusters",
                    }
                },
                {"$project": {"pca": 0, "tsne": 0}},
            ]
        )

    pipeline += [
        {"$sort": {"created_at": -1}},
    ]
    clusterings = (
        await mongo_db["private-clusterings"].aggregate(pipeline).to_list(length=limit)
    )
    if not clusterings:
        return []
    valid_clusterings = [
        Clustering.model_validate(clustering) for clustering in clusterings
    ]
    return valid_clusterings


async def fetch_all_clusters(
    project_id: str, clustering_id: Optional[str] = None, limit: int = 100
) -> List[Cluster]:
    """
    Fetch the clusters of a project.

    If the clustering (group of clusters) is not specified, the latest clustering is used.
    """
    mongo_db = await get_mongo_db()
    # Get the latest clustering
    if clustering_id is None:
        get_latest_clustering = (
            await mongo_db["private-clusterings"]
            .find({"project_id": project_id})
            .sort([("created_at", -1)])
            .to_list(length=1)
        )
        if len(get_latest_clustering) == 0:
            return []
        latest_clustering = get_latest_clustering[0]
        clustering_id = latest_clustering.get("id")

    # Retrieve the clusters of the clustering
    clusters = (
        await mongo_db["private-clusters"]
        .find(
            {
                "project_id": project_id,
                "clustering_id": clustering_id,
            }
        )
        .to_list(length=limit)
    )
    valid_clusters = [Cluster.model_validate(cluster) for cluster in clusters]
    return valid_clusters


async def fetch_single_cluster(project_id: str, cluster_id: str) -> Optional[Cluster]:
    """
    Fetch a single cluster from a project
    """
    mongo_db = await get_mongo_db()
    cluster = await mongo_db["private-clusters"].find_one(
        {"project_id": project_id, "id": cluster_id}
    )
    if cluster is None:
        return None
    valid_cluster = Cluster.model_validate(cluster)
    return valid_cluster


async def nb_items_with_a_metadata_field(
    project_id: str, collection_name: str, metadata_field: str
) -> int:
    """
    Get the count of items in a collection that have a specific metadata field value.
    """

    mongo_db = await get_mongo_db()

    try:
        # Count the number of different user ids in the tasks metadata
        nb_items = await mongo_db[collection_name].distinct(
            f"metadata.{metadata_field}",
            {"project_id": project_id, f"metadata.{metadata_field}": {"$ne": None}},
        )

        return len(nb_items)

    except Exception as e:
        logger.warning(
            f"Failed to fetch the number of {metadata_field} in collection {collection_name} for project {project_id}: {e}",
        )
        return 0


async def compute_successrate_metadata_quantiles(
    project_id: str,
    metadata_field: str,
    collection_name: str = "tasks",
    quantile_value: float = 0.1,
) -> Tuple[float, float, float]:
    """
    Get the success rate of items in a collection that have a specific metadata field value.
    """

    mongo_db = await get_mongo_db()

    pipeline = [
        {
            "$match": {
                "flag": {"$in": ["success", "failure"]},
                "project_id": project_id,
                f"metadata.{metadata_field}": {"$exists": True},
                "_id": f"$metadata.{metadata_field}",
            }
        },
        {
            "$set": {
                "averageScore": {
                    "$avg": {"$cond": [{"$eq": ["$flag", "success"]}, 1, 0]}
                },
            }
        },
        {
            "$project": {
                "bottomQuantile": {
                    "$percentile": {
                        "input": "$averageScore",
                        "p": [quantile_value],
                        "method": "approximate",
                    }
                },
                "averageScore": {
                    "$avg": "$averageScore",
                },
                "topQuantile": {
                    "$percentile": {
                        "input": "$averageScore",
                        "p": [(1 - quantile_value)],
                        "method": "approximate",
                    }
                },
            }
        },
    ]

    # Get the value of the top and bottom quantiles
    result = await mongo_db[collection_name].aggregate(pipeline).to_list(length=None)

    # Add checks on the result length
    if len(result) == 0:
        logger.warning(
            f"No {metadata_field} found in collection {collection_name} for project {project_id}"
        )
        return 0.0, 0.0, 0.0

    bottom_quantile = result[0]["bottomQuantile"]
    average = result[0]["averageScore"]
    top_quantile = result[0]["topQuantile"]

    if result:
        return bottom_quantile, average, top_quantile
    else:
        return 0.0, 0.0, 0.0


async def compute_nb_items_with_metadata_field(
    project_id: str,
    metadata_field: str,
    collection_name: str,
    quantile_value: float = 0.1,
) -> Tuple[int, float, int]:
    """
    Get the number of items in a collection that have a specific metadata field value.
    Returns a tupple of (bottom quantile, average, top quantile) count.
    """

    mongo_db = await get_mongo_db()

    try:
        pipeline = [
            # Match on the project id and the existence of the metadata field
            {
                "$match": {
                    "project_id": project_id,
                    f"metadata.{metadata_field}": {"$exists": True, "$ne": None},
                }
            },
            {
                "$group": {
                    "_id": "$user_id",  # Group by 'user_id'
                    "count": {"$sum": 1},  # Count the documents in each group
                }
            },
            {
                "$sort": {"count": -1}  # Sort by 'count' in descending order
            },
        ]

        # Execute the aggregation pipeline
        results = []  # List to hold the results
        async for group in mongo_db[collection_name].aggregate(pipeline):
            results.append(group["count"])

        logger.debug(
            f"Results for {metadata_field} in collection {collection_name} for project {project_id}: {results}"
        )

        # If no results, return 0
        if len(results) == 0:
            return 0, 0.0, 0

        # Get the average and the quantiles
        average = sum(results) / len(results)
        bottom_quantile = results[int(len(results) * quantile_value)]
        top_quantile = results[int(len(results) * (1 - quantile_value))]

        return bottom_quantile, average, top_quantile

    except Exception as e:
        logger.warning(
            f"Failed to fetch the number of {metadata_field} in collection {collection_name} for project {project_id}: {e}",
        )
        return 0, 0.0, 0


async def compute_session_length_per_metadata(
    project_id: str,
    metadata_field: str = "user_id",
    quantile_value: float = 0.1,
) -> Tuple[float, float, float]:
    """
    Get the quantiles and average length of sessions in number of tasks for a specific metadata field value.
    Returns a tupple of (bottom quantile, average, top quantile) count.
    """

    mongo_db = await get_mongo_db()

    try:
        pipeline = [
            # Match on the project id and the existence of the metadata field
            {
                "$match": {
                    "project_id": project_id,
                    "session_id": {"$exists": True, "$ne": None},
                    f"metadata.{metadata_field}": {"$exists": True, "$ne": None},
                }
            },
            {
                "$group": {
                    "_id": {
                        "session_id": "$session_id",
                        metadata_field: f"$metadata.{metadata_field}",
                    },
                    "taskCount": {"$sum": 1},
                }
            },
            {
                "$group": {
                    "_id": f"$_id.{metadata_field}",
                    "averageSessionLength": {"$avg": "$taskCount"},
                }
            },
        ]

        # Execute the aggregation pipeline
        results = []  # List to hold the results
        async for group in mongo_db["tasks"].aggregate(pipeline):
            results.append(group["averageSessionLength"])

        logger.debug(
            f"Results for {metadata_field} in collection sessions for project {project_id}: {results}"
        )

        # If no results, return 0
        if len(results) == 0:
            return 0, 0.0, 0

        # Get the average and the quantiles
        average = sum(results) / len(results)

        # Handle the cases where len(results) is 1 or 2
        if len(results) == 1:
            bottom_quantile = results[0]
            top_quantile = results[0]
        elif len(results) == 2:
            bottom_quantile = results[0]
            top_quantile = results[1]
        else:
            bottom_quantile = results[int(len(results) * quantile_value)]
            top_quantile = results[int(len(results) * (1 - quantile_value))]

        return bottom_quantile, average, top_quantile

    except Exception as e:
        logger.warning(
            f"Failed to fetch the session length for {metadata_field} in collection sessions for project {project_id}: {e}",
        )
        return 0, 0.0, 0


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
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
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

    query_result = await mongo_db["events"].find(main_filter).to_list(length=None)
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
    logger.debug(f"DataFrame: {df['confirmed']}")
    if event_type == "confidence":
        mask_y_pred_true = (
            (
                (df["source"] != "owner")
                & (df["confirmed"])
                & (~df["removed"])
                & (df["score_range"].notna())
            )
            | (
                (df["source"] != "owner")
                & (df["confirmed"])
                & (~df["removed"])
                & (df["score_range"].notna())
            )
            | (
                (df["source"] != "owner")
                & (~df["confirmed"])
                & (df["removed"])
                & (df["score_range"].notna())
            )
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
            (
                (df["source"] != "owner")
                & (df["confirmed"])
                & (~df["removed"])
                & (df["score_range"].notna())
            )
            | (
                (df["source"] != "owner")
                & (df["confirmed"])
                & (~df["removed"])
                & (df["score_range"].notna())
            )
            | (
                (df["source"] != "owner")
                & (~df["confirmed"])
                & (df["removed"])
                & (df["score_range"].notna())
            )
            | (
                (df["source"] == "owner")
                & (~df["confirmed"])
                & (~df["removed"])
                & (df["score_range"].notna())
            )
            | (
                (df["source"] == "owner")
                & (df["confirmed"])
                & (~df["removed"])
                & (df["score_range"].notna())
            )
            | (
                (df["source"] == "owner")
                & (df["confirmed"])
                & (df["removed"])
                & (df["score_range"].notna())
            )
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
        ) | (
            (df["source"] != "owner")
            & (df["confirmed"])
            & (~df["removed"])
            & (df["score_range"].notna())
        )

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
    logger.debug(f"Filters: {filters}")
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
                output["mean_squared_error"] = mean_squared_error(y_true, y_pred)
            if "r_squared" in metrics:
                output["r_squared"] = r2_score(y_true, y_pred)
            if "f1_score_binary" in metrics:
                output["f1_score_binary"] = f1_score(y_true, y_pred)
            if "precision_binary" in metrics:
                output["precision_binary"] = precision_score(y_true, y_pred)
            if "recall_binary" in metrics:
                output["recall_binary"] = recall_score(y_true, y_pred)
            if "f1_score_multiclass" in metrics:
                output["f1_score_multiclass"] = f1_score(
                    y_true, y_pred, average="weighted"
                )
            if "precision_multiclass" in metrics:
                output["precision_multiclass"] = precision_score(
                    y_true, y_pred, average="weighted"
                )
            if "recall_multiclass" in metrics:
                output["recall_multiclass"] = recall_score(
                    y_true, y_pred, average="weighted"
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
    # Add missing days to the result, and set the missing values to 0
    result = pd.DataFrame(result)
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
        result["success"] = 0
        result["failure"] = 0
        result["undefined"] = 0

    return result.to_dict(orient="records")


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


async def fetch_flattened_tasks(
    project_id: str,
    limit: Optional[int] = 1000,
    with_events: bool = True,
    with_sessions: bool = True,
    pagination: Optional[Pagination] = None,
    with_removed_events: bool = False,
) -> List[FlattenedTask]:
    """
    Get a flattened representation of the tasks of a project for analytics

    The with_events parameter allows to include the events in the result.
    The with_sessions parameter allows to include the session length in the result.
    The with_removed_events parameter allows to include the removed events in the result ; if with_events is False, this parameter is ignored.
    """

    if not with_events and with_removed_events:
        logger.warning(
            "The with_removed_events parameter is ignored if with_events is False"
        )

    # Create an aggregated table
    mongo_db = await get_mongo_db()

    # Aggregation pipeline
    pipeline: List[Dict[str, object]] = [
        {"$match": {"project_id": project_id}},
    ]
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

    if with_sessions:
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "sessions",
                        "localField": "session_id",
                        "foreignField": "id",
                        "as": "session",
                    }
                },
                {"$unwind": {"path": "$session", "preserveNullAndEmptyArrays": True}},
            ]
        )
        return_columns = {
            **return_columns,
            "session_length": "$session.session_length",
        }

    if with_events:
        if not with_removed_events:
            pipeline.extend(
                [
                    {
                        "$lookup": {
                            "from": "events",
                            "localField": "id",
                            "foreignField": "task_id",
                            "as": "events",
                        },
                    },
                    # Deduplicate events based on event_name
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
                                                            "$$this.event_name",
                                                            "$$value.event_name",
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
                    {
                        "$unwind": {
                            "path": "$events",
                            "preserveNullAndEmptyArrays": True,
                        }
                    },
                ]
            )

        # Query Mongo
        else:
            pipeline.extend(
                [
                    {
                        "$lookup": {
                            "from": "events",
                            "localField": "id",
                            "foreignField": "task_id",
                            "as": "events",
                        },
                    },
                    {
                        "$addFields": {
                            "events": {
                                "$filter": {
                                    "input": "$events",
                                    "as": "event",
                                    "cond": {
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
                    {
                        "$unwind": {
                            "path": "$events",
                            "preserveNullAndEmptyArrays": True,
                        }
                    },
                ]
            )

        return_columns = {
            **return_columns,
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

        if with_removed_events:
            return_columns = {
                **return_columns,
                "event_removed": "$events.removed",
                "event_removal_reason": "$events.removal_reason",
            }

    # Sort the pipeline
    pipeline.extend(
        [
            {"$project": return_columns},
            {"$sort": {"task_created_at": -1}},
        ]
    )

    # Pagination

    if pagination:
        pipeline.extend(
            [
                {"$skip": pagination.page * pagination.per_page},
                {"$limit": pagination.per_page},
            ]
        )

    # Limit
    else:
        pipeline.extend(
            [
                {"$limit": limit},
            ]
        )

    # Query Mongo
    flattened_tasks = await mongo_db["tasks"].aggregate(pipeline).to_list(length=limit)

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

    return new_flattened_tasks


async def update_from_flattened_tasks(
    org_id: str,
    project_id: str,
    flattened_tasks: List[FlattenedTask],
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
    project_ids_in_db = set(
        [project_id["project_id"] for project_id in project_ids_in_db]
    )
    # If the intersection is not empty, it means that the task_id belong to another project
    if project_ids_in_db - {project_id} != set():
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to tasks not in project {project_id}",
        )

    # A single row is a combination of task x event x eval
    # TODO : Infer the granularity from the available non-None columns

    task_update: Dict[str, Dict[str, object]] = defaultdict(dict)
    eval_create_statements = []
    for task in flattened_tasks:
        if task.task_metadata is not None:
            task_update[task.task_id]["metadata"] = task.task_metadata
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


async def get_ab_tests_versions(
    project_id: str,
    versionA: Optional[str],
    versionB: Optional[str],
    selected_events_ids: Optional[List[str]] = None,
) -> List[Dict[str, Union[str, float, int]]]:
    """
    - For boolean events, gets the number of times the event was detected in each task with the two versions of the model.
    - For categorical events, gets the number of times each category was detected in each task with the two versions of the model.
    - For range evnts, shows the average value of the score for each task with the two versions of the model.
    """
    mongo_db = await get_mongo_db()
    collection_name = "events"

    logger.debug(f"Fetching AB tests for project {project_id}")
    logger.debug(f"Versions: {versionA} and {versionB}")

    if versionA == "None":
        versionA = None
    if versionB == "None":
        versionB = None

    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                "removed": {"$ne": ["$events.removed", True]},
            }
        },
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
            "$match": {
                "task.metadata.version_id": {"$in": [versionA, versionB]},
            }
        },
        {
            "$group": {
                "_id": {
                    "version_id": "$task.metadata.version_id",
                    "event_definition_id": "$event_definition.id",
                    "event_label": "$score_range.label",
                    "event_name": "$event_definition.event_name",
                    "event_type": "$event_definition.score_range_settings.score_type",
                },
                "count": {"$sum": 1},
                "score": {"$avg": "$score_range.value"},
            },
        },
        # Keep only the events that are in the selected_events_id list
        {
            "$match": {
                "_id.event_definition_id": {"$in": selected_events_ids},
            },
        },
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

    results = await mongo_db[collection_name].aggregate(pipeline).to_list(length=None)
    if not results or len(results) == 0:
        logger.info("No results found")
        return []

    # This dict will have event_names as keys, and the values will be dictionnaries with the version_id as keys and the count as values
    total_tasks_with_A = await mongo_db["tasks"].count_documents(
        {"project_id": project_id, "metadata.version_id": versionA}
    )
    if total_tasks_with_A == 0:
        logger.info(f"No tasks found for version {versionA}")
        return []

    total_tasks_with_B = await mongo_db["tasks"].count_documents(
        {"project_id": project_id, "metadata.version_id": versionB}
    )
    if total_tasks_with_B == 0:
        logger.info(f"No tasks found for version {versionB}")
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
                versionA: values.get(versionA, 0) / total_tasks_with_A,
                versionB: values.get(versionB, 0) / total_tasks_with_B,
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


async def compute_cloud_of_clusters(
    project_id: str,
    version: ClusteringEmbeddingCloud,
) -> dict:
    """
    Get the embeddings for the clustering project.
    Compute a PCA on the embeddings and return the first three components if the version is PCA.
    Compute a TSNE on the embeddings and return the first three components if the version is TSNE.
    """
    if version.type != "pca":
        raise NotImplementedError(f"Type {version.type} is not implemented")

    mongo_db = await get_mongo_db()
    collection_name = "private-clusterings"
    pipeline: List[Dict[str, object]] = [
        {
            "$match": {
                "project_id": project_id,
                "id": version.clustering_id,
                version.type: {"$exists": True},
            }
        },
    ]

    raw_results = await mongo_db[collection_name].aggregate(pipeline).to_list(length=1)
    if raw_results is None or raw_results == []:
        return {}

    clustering_model = Clustering.model_validate(raw_results[0])

    # Check if the clustering model has the required field
    if version.type == "pca":
        cloud_of_points = clustering_model.pca
    if version.type == "tsne":
        cloud_of_points = clustering_model.tsne
    # TODO: If new type of embedding is added, add the corresponding code here

    # If the clustering isn't finished, cloud_of_points is None. Return early
    if cloud_of_points is None or cloud_of_points == {}:
        return {}

    if "clusters_names" in cloud_of_points.keys():
        # Old data model
        dim_reduction_results = cloud_of_points
    else:
        # New model.
        # TODO : Version the models in cloud_of_point
        # Get the task_id or the session_id from the embeddings_ids in raw_results[0]["pca"]
        collection_name = "private-embeddings"
        embeddings_ids = cloud_of_points["embeddings_ids"]
        pipeline = [
            {
                "$match": {
                    "project_id": project_id,
                    "id": {"$in": embeddings_ids},
                }
            },
            {"$project": {"task_id": 1, "session_id": 1, "user_id": 1}},
        ]

        scope_ids = (
            await mongo_db[collection_name].aggregate(pipeline).to_list(length=None)
        )
        if clustering_model.scope == "messages":
            scope_ids = [scope_id["task_id"] for scope_id in scope_ids]
        elif clustering_model.scope == "sessions":
            scope_ids = [scope_id["session_id"] for scope_id in scope_ids]
        elif clustering_model.scope == "users":
            scope_ids = [scope_id["user_id"] for scope_id in scope_ids]

        # Get the clusters names from the clusters_ids in raw_results[0]["pca"]
        # I want a cluster name for each cluster_id
        collection_name = "private-clusters"
        pipeline = [
            {
                "$match": {
                    "project_id": project_id,
                    "id": {"$in": cloud_of_points["clusters_ids"]},
                }
            },
            {"$project": {"name": 1, "id": 1}},
        ]

        clusters_ids_to_clusters_names = (
            await mongo_db[collection_name].aggregate(pipeline).to_list(length=None)
        )
        clusters_ids_to_clusters_names = {
            cluster_id_to_cluster_name["id"]: cluster_id_to_cluster_name["name"]
            for cluster_id_to_cluster_name in clusters_ids_to_clusters_names
        }

        clusters_names = [
            clusters_ids_to_clusters_names[cluster_id]
            for cluster_id in cloud_of_points["clusters_ids"]
        ]
        dim_reduction_results = cloud_of_points
        del dim_reduction_results["embeddings_ids"]
        dim_reduction_results["ids"] = scope_ids
        dim_reduction_results["clusters_names"] = clusters_names

    return dim_reduction_results


async def get_clustering_by_id(
    project_id: str,
    clustering_id: str,
    fetch_clouds: bool = False,
) -> Clustering:
    """
    Get a clustering based on its id.

    If fetch_clouds is False, the pca and tsne fields are not returned. This is useful when the embeddings are not needed.
    """
    mongo_db = await get_mongo_db()
    collection_name = "private-clusterings"
    pipeline: List[Dict[str, object]] = [
        {
            "$match": {
                "project_id": project_id,
                "id": clustering_id,
            }
        },
    ]
    if not fetch_clouds:
        pipeline.append({"$project": {"_id": 0, "pca": 0, "tsne": 0}})

    raw_results = await mongo_db[collection_name].aggregate(pipeline).to_list(length=1)
    if raw_results is None or raw_results == []:
        raise HTTPException(
            status_code=404,
            detail=f"Clustering {clustering_id} not found in project {project_id}",
        )

    clustering_model = Clustering.model_validate(raw_results[0])
    return clustering_model


async def get_total_nb_of_users(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
) -> Optional[int]:
    """
    Get the total number of unique users for a project.
    This is the number of unique user_id in the tasks.
    """

    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id, filters=filters, fetch_objects="tasks"
    )
    pipeline = await query_builder.build()

    # We count the number of unique user_id
    pipeline += [
        # Tasks may not have a user_id, so we filter this case
        {"$match": {"metadata.user_id": {"$exists": True, "$ne": None}}},
        {
            "$group": {
                "_id": "$metadata.user_id",
            }
        },
        {"$count": "total_users"},
    ]

    query_result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=1)

    if len(query_result) == 0:
        return None

    total_nb_users = query_result[0]["total_users"]
    return total_nb_users


async def get_nb_users_messages(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
    limit: Optional[int] = None,
) -> Optional[int]:
    """
    Get the total number of messages sent by unique users for a project.

    This is used to get all the messages sent by active users, according to the filters.
    """

    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id, filters=filters, fetch_objects="tasks"
    )
    pipeline = await query_builder.build()

    # We fetch the list of active users ids first
    pipeline += [
        {"$match": {"metadata.user_id": {"$exists": True, "$ne": None}}},
        {
            "$group": {
                "_id": "$metadata.user_id",
            }
        },
    ]
    query_result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=limit)
    if len(query_result) == 0:
        return None
    active_user_ids: List[str] = [user["_id"] for user in query_result]

    # Then, we find how many messages these users sent in total, during their whole existence
    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                "metadata.user_id": {"$in": active_user_ids},
            }
        },
        {
            "$count": "nb_users_messages",
        },
    ]
    query_result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=1)
    if len(query_result) == 0:
        return None

    total_nb_users_messages = query_result[0]["nb_users_messages"]

    return total_nb_users_messages

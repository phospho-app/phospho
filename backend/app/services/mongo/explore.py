"""
Explore metrics service
"""

import datetime
from collections import defaultdict
from typing import Dict, List, Literal, Optional, Tuple, Union

import pandas as pd
import pydantic

# Models
from app.api.platform.models import ABTest, Topics, ProjectDataFilters
from app.db.models import Eval, FlattenedTask
from app.db.mongo import get_mongo_db
from app.services.mongo.projects import (
    get_all_events,
    get_all_tasks,
)
from app.services.mongo.sessions import compute_session_length
from app.utils import generate_timestamp, get_last_week_timestamps
from fastapi import HTTPException
from loguru import logger
from pymongo import InsertOne, UpdateOne


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
        tasks = await get_all_tasks(
            project_id=project_id,
            limit=limit,
            flag_filter=filters.flag,
            event_name_filter=filters.event_name,
            last_eval_source_filter=filters.last_eval_source,
            metadata_filter=filters.metadata,
            created_at_start=filters.created_at_start,
            created_at_end=filters.created_at_end,
            # tasks_filter=tasks_filter,
        )
        df = pd.DataFrame([task.model_dump() for task in tasks])
    if count_of == "events":
        events = await get_all_events(
            project_id=project_id,
            limit=limit,
            events_filter=filters,
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
    quantile_filter: Optional[float] = None,
    flag_filter: Optional[Literal["success", "failure"]] = None,
    event_name_filter: Optional[Union[str, List[str]]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
) -> Optional[Dict[str, object]]:
    """
    Compute the success rate per message position. Used for the Tasks and the Sessions dashboard.
    We only keep the 90% percentile of the messages length to avoid outliers with very long sessions.

    Return None if there is no session_id in the tasks.
    """
    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {"project_id": project_id}
    if created_at_start is not None:
        main_filter["created_at"] = {"$gte": created_at_start}
    if created_at_end is not None:
        main_filter["created_at"] = {"$lte": created_at_end}
    pipeline = [
        {"$match": main_filter},
        # Find tasks
        {
            "$lookup": {
                "from": "tasks",
                "localField": "id",
                "foreignField": "session_id",
                "as": "tasks",
            }
        },
    ]
    if event_name_filter is not None:
        pipeline.append(
            {
                "$match": {
                    "$and": [
                        {"tasks.events": {"$ne": []}},
                        {
                            "tasks.events": {
                                "$elemMatch": {"event_name": {"$in": event_name_filter}}
                            }
                        },
                    ]
                },
            },
        )
    tasks_filter: Dict[str, object] = {"tasks": {"$ne": []}}
    # Filter on the flag
    if flag_filter is not None:
        # The below filter is just "a session that has at least 1 task with the flag"
        # tasks_filter["tasks.flag"] = flag_filter
        logger.debug("Flag filter for success rate per task position has no effect.")
    pipeline.append(
        {"$match": tasks_filter},
    )
    result = (
        await mongo_db["sessions"]
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


async def get_total_nb_of_tasks(
    project_id: str,
    flag_filter: Optional[Literal["success", "failure"]] = None,
    event_name_filter: Optional[List[str]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
) -> Optional[int]:
    """
    Get the total number of tasks of a project.
    """
    mongo_db = await get_mongo_db()
    # Time range filter
    global_filters: Dict[str, object] = {"project_id": project_id}
    if created_at_start is not None:
        global_filters["created_at"] = {"$gte": created_at_start}
    if created_at_end is not None:
        global_filters["created_at"] = {"$lte": created_at_end}

    # Other filters
    if flag_filter is None and event_name_filter is None:
        total_nb_tasks = await mongo_db["tasks"].count_documents(global_filters)
    elif flag_filter is not None and event_name_filter is None:
        global_filters["flag"] = flag_filter
        total_nb_tasks = await mongo_db["tasks"].count_documents(global_filters)
    elif event_name_filter is not None:
        # Do an aggregate query
        if flag_filter is not None:
            global_filters["flag"] = flag_filter
        global_filters["$and"] = [
            {"events": {"$ne": []}},
            {"events": {"$elemMatch": {"event_name": {"$in": event_name_filter}}}},
        ]
        query_result = (
            await mongo_db["tasks"]
            .aggregate(
                [
                    {"$match": global_filters},
                    {"$count": "nb_tasks"},
                ]
            )
            .to_list(length=1)
        )
        if query_result is not None and len(query_result) > 0:
            total_nb_tasks = query_result[0]["nb_tasks"]
        else:
            total_nb_tasks = None
    return total_nb_tasks


async def get_total_success_rate(
    project_id: str,
    flag_filter: Optional[Literal["success", "failure"]] = None,
    event_name_filter: Optional[Union[str, List[str]]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
) -> Optional[float]:
    """
    Get the total success rate of a project. This is the ratio of successful tasks over
    the total number of tasks.
    """

    mongo_db = await get_mongo_db()
    main_filter = {"project_id": project_id}
    # Filter on the flag
    if flag_filter is not None:
        main_filter["flag"] = flag_filter
    # Time range filter
    if created_at_start is not None:
        main_filter["created_at"] = {"$gte": created_at_start}
    if created_at_end is not None:
        main_filter["created_at"] = {"$lte": created_at_end}
    pipeline: List[Dict[str, object]] = [
        {"$match": main_filter},
    ]
    # Filter on the event name
    if event_name_filter is not None:
        pipeline.append(
            {
                "$match": {
                    "$and": [
                        {"events": {"$ne": []}},
                        {
                            "events": {
                                "$elemMatch": {"event_name": {"$in": event_name_filter}}
                            }
                        },
                    ]
                }
            },
        )
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
    logger.info(f"result: {result}")
    if len(result) == 0:
        # No tasks = success rate is None
        return None
    total_success_rate = result[0]["global_success_rate"]
    return total_success_rate


async def get_most_detected_event_name(
    project_id: str,
    flag_filter: Optional[Literal["success", "failure"]] = None,
    event_name_filter: Optional[Union[str, List[str]]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
) -> Optional[str]:
    """
    Get the most detected event name of a project.
    """
    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {"project_id": project_id}
    # Filter on the event name
    if event_name_filter is not None:
        main_filter["event_name"] = {"$in": event_name_filter}
    # Time range filter
    if created_at_start is not None:
        main_filter["created_at"] = {"$gte": created_at_start}
    if created_at_end is not None:
        main_filter["created_at"] = {"$lte": created_at_end}
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
    # Filter on the flag
    if flag_filter is not None:
        pipeline.append(
            {"$match": {"tasks.flag": flag_filter}},
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


async def get_nb_of_daily_tasks(
    project_id: str,
    start_timestamp: int,
    end_timestamp: int,
    flag_filter: Optional[Literal["success", "failure"]] = None,
    event_name_filter: Optional[Union[str, List[str]]] = None,
) -> List[dict]:
    """
    Get the number of daily tasks of a project.
    """
    if isinstance(event_name_filter, str):
        event_name_filter = [event_name_filter]
    tasks = await get_all_tasks(
        project_id=project_id,
        limit=None,
        flag_filter=flag_filter,
        event_name_filter=event_name_filter,
        created_at_start=start_timestamp,
        created_at_end=end_timestamp,
    )
    df = pd.DataFrame([task.model_dump() for task in tasks])
    complete_date_range = pd.date_range(
        datetime.datetime.fromtimestamp(start_timestamp, datetime.timezone.utc),
        datetime.datetime.fromtimestamp(end_timestamp, datetime.timezone.utc),
        freq="D",
    )
    complete_df = pd.DataFrame({"date": complete_date_range})

    if not df.empty:
        df["date"] = pd.to_datetime(df["created_at"], unit="s", utc=True).dt.date
        # Group by date and count
        nb_tasks_per_day = (
            df.groupby(["date"])
            .count()
            .reset_index()[["date", "id"]]
            .rename(columns={"id": "nb_tasks"})
        )

        # Add missing days

        complete_df["date"] = pd.to_datetime(complete_df["date"]).dt.date
        nb_tasks_per_day = pd.merge(
            complete_df, nb_tasks_per_day, on="date", how="left"
        ).fillna(0)
    else:
        nb_tasks_per_day = complete_df
        nb_tasks_per_day["nb_tasks"] = 0

    return nb_tasks_per_day[["date", "nb_tasks"]].to_dict(orient="records")


async def get_top_event_names_and_count(
    project_id: str,
    limit: int = 3,
    start_timestamp: Optional[int] = None,
    end_timestamp: Optional[int] = None,
    flag_filter: Optional[Literal["success", "failure"]] = None,
    event_name_filter: Optional[Union[str, List[str]]] = None,
) -> List[Dict[str, object]]:
    """
    Get the top event names and count of a project.
    """
    mongo_db = await get_mongo_db()
    if start_timestamp is None:
        start_timestamp = 0
    if end_timestamp is None:
        end_timestamp = generate_timestamp()

    main_filter = {
        "project_id": project_id,
        "created_at": {
            "$gte": start_timestamp,
            "$lte": end_timestamp,
        },
    }
    if event_name_filter is not None:
        main_filter["event_name"] = {"$in": event_name_filter}
    # Event is not removed
    main_filter["removed"] = {"$ne": True}
    # Either the remove filed doesn't exist, either it's not True
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
    if flag_filter is not None:
        pipeline.append(
            {"$match": {"tasks.flag": flag_filter}},
        )
    pipeline.extend(
        [
            # Deduplicate the events by task_id and event_name
            {"$group": {"_id": {"task_id": "$task_id", "event_name": "$event_name"}}},
            {"$group": {"_id": "$_id.event_name", "nb_events": {"$sum": 1}}},
            {"$project": {"_id": 0, "event_name": "$_id", "nb_events": 1}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
    )
    result = await mongo_db["events"].aggregate(pipeline).to_list(length=limit)

    return result


async def get_daily_success_rate(
    project_id: str,
    start_timestamp: int,
    end_timestamp: int,
    flag_filter: Optional[Literal["success", "failure"]] = None,
    event_name_filter: Optional[Union[str, List[str]]] = None,
) -> List[dict]:
    """
    Get the daily success rate of a project.
    """
    mongo_db = await get_mongo_db()
    main_filter = {
        "project_id": project_id,
        "created_at": {"$gte": start_timestamp, "$lte": end_timestamp},
    }
    if flag_filter is not None:
        main_filter["flag"] = flag_filter
    pipeline: List[Dict[str, object]] = [
        {"$match": main_filter},
    ]
    if event_name_filter is not None:
        pipeline.append(
            {
                "$match": {
                    "$and": [
                        {"events": {"$ne": []}},
                        {
                            "events": {
                                "$elemMatch": {"event_name": {"$in": event_name_filter}}
                            }
                        },
                    ]
                },
            },
        )
    # Add the success rate computation
    pipeline.extend(
        [
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
    )
    result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)

    df = pd.DataFrame(result)

    complete_date_range = pd.date_range(
        datetime.datetime.fromtimestamp(start_timestamp, datetime.timezone.utc),
        datetime.datetime.fromtimestamp(end_timestamp, datetime.timezone.utc),
        freq="D",
    )
    complete_df = pd.DataFrame({"date": complete_date_range})
    complete_df["date"] = pd.to_datetime(complete_df["date"]).dt.date

    if not df.empty:
        df["date"] = pd.to_datetime(df["created_at"], unit="s", utc=True).dt.date
        # Group by date and count
        daily_success_rate = (
            df.groupby(["date"])[["is_success"]]
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
    flag_filter: Optional[str] = None,
    event_name_filter: Optional[List[str]] = None,
    metrics: Optional[List[str]] = None,
    quantile_filter: Optional[float] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
) -> Dict[str, object]:
    """
    Compute aggregated metrics for the tasks of a project. Used for the Tasks dashboard.
    """
    if await project_has_tasks(project_id) is False:
        return {}

    if metrics is None:
        metrics = [
            "total_nb_tasks",
            "global_success_rate",
            "most_detected_event",
            "nb_daily_tasks",
            "events_ranking",
            "daily_success_rate",
            "success_rate_per_task_position",
        ]

    today_datetime = datetime.datetime.now(datetime.timezone.utc)
    today_timestamp = int(today_datetime.timestamp())
    seven_days_ago_datetime = today_datetime - datetime.timedelta(days=6)
    # Round to the beginning of the day
    seven_days_ago_datetime = seven_days_ago_datetime.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    seven_days_ago_timestamp = int(seven_days_ago_datetime.timestamp())

    output: Dict[str, object] = {}

    if "total_nb_tasks" in metrics:
        output["total_nb_tasks"] = await get_total_nb_of_tasks(
            project_id=project_id,
            flag_filter=flag_filter,
            event_name_filter=event_name_filter,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
        )
    if "global_success_rate" in metrics:
        output["global_success_rate"] = await get_total_success_rate(
            project_id=project_id,
            flag_filter=flag_filter,
            event_name_filter=event_name_filter,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
        )
    if "most_detected_event" in metrics:
        output["most_detected_event"] = await get_most_detected_event_name(
            project_id=project_id,
            flag_filter=flag_filter,
            event_name_filter=event_name_filter,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
        )
    if "nb_daily_tasks" in metrics:
        output["nb_daily_tasks"] = await get_nb_of_daily_tasks(
            project_id=project_id,
            start_timestamp=seven_days_ago_timestamp,
            end_timestamp=today_timestamp,
            flag_filter=flag_filter,
            event_name_filter=event_name_filter,
        )
    if "events_ranking" in metrics:
        output["events_ranking"] = await get_top_event_names_and_count(
            project_id=project_id,
            limit=3,
            start_timestamp=seven_days_ago_timestamp,
            end_timestamp=today_timestamp,
            flag_filter=flag_filter,
            event_name_filter=event_name_filter,
        )
    if "daily_success_rate" in metrics:
        output["daily_success_rate"] = await get_daily_success_rate(
            project_id=project_id,
            start_timestamp=seven_days_ago_timestamp,
            end_timestamp=today_timestamp,
            flag_filter=flag_filter,
            event_name_filter=event_name_filter,
        )
    if "success_rate_per_task_position" in metrics:
        output[
            "success_rate_per_task_position"
        ] = await get_success_rate_per_task_position(
            project_id=project_id,
            quantile_filter=quantile_filter,
            flag_filter=flag_filter,
            event_name_filter=event_name_filter,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
        )

    return output


async def get_total_nb_of_sessions(
    project_id: str,
    event_name_filter: Optional[List[str]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
) -> int:
    """
    Get the total number of sessions of a project.
    """
    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {"project_id": project_id}
    # Time range filter
    if created_at_start is not None:
        main_filter["created_at"] = {"$gte": created_at_start}
    if created_at_end is not None:
        main_filter["created_at"] = {"$lte": created_at_end}
    if event_name_filter is None:
        total_nb_sessions = await mongo_db["sessions"].count_documents(main_filter)
    else:
        # Do an aggregate query
        query_result = (
            await mongo_db["sessions"]
            .aggregate(
                [
                    {"$match": main_filter},
                    {
                        "$match": {
                            "$and": [
                                {"events": {"$ne": []}},
                                {
                                    "events": {
                                        "$elemMatch": {
                                            "event_name": {"$in": event_name_filter}
                                        }
                                    }
                                },
                            ]
                        }
                    },
                    {"$count": "nb_sessions"},
                ]
            )
            .to_list(length=1)
        )
        if query_result is not None and len(query_result) > 0:
            total_nb_sessions = query_result[0]["nb_sessions"]
        else:
            total_nb_sessions = 0
    return total_nb_sessions


async def get_global_average_session_length(
    project_id: str,
    event_name_filter: Optional[List[str]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
) -> float:
    """
    Get the global average session length of a project.
    """
    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {
        "project_id": project_id,
        "session_id": {"$ne": None},
    }
    # Time range filter
    if created_at_start is not None:
        main_filter["created_at"] = {"$gte": created_at_start}
    if created_at_end is not None:
        main_filter["created_at"] = {"$lte": created_at_end}
    pipeline: List[Dict[str, object]] = [
        {"$match": main_filter},
    ]
    if event_name_filter is not None:
        pipeline.append(
            {
                "$match": {
                    "$and": [
                        {"events": {"$ne": []}},
                        {
                            "events": {
                                "$elemMatch": {"event_name": {"$in": event_name_filter}}
                            }
                        },
                    ]
                },
            },
        )
    result = (
        await mongo_db["tasks"]
        .aggregate(
            pipeline
            + [
                {
                    "$group": {
                        "_id": "$session_id",
                        "nb_tasks": {"$sum": 1},
                    }
                },
                {"$group": {"_id": None, "avg_session_length": {"$avg": "$nb_tasks"}}},
                {"$project": {"_id": 0, "avg_session_length": 1}},
            ]
        )
        .to_list(length=1)
    )
    if len(result) == 0:
        return 0
    global_average_session_length = result[0]["avg_session_length"]
    return global_average_session_length


async def get_last_message_success_rate(
    project_id: str,
    event_name_filter: Optional[List[str]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
) -> float:
    """
    Get the success rate of the last message of a project.
    """
    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {"project_id": project_id}
    # Time range filter
    if created_at_start is not None:
        main_filter["created_at"] = {"$gte": created_at_start}
    if created_at_end is not None:
        main_filter["created_at"] = {"$lte": created_at_end}
    pipeline: List[Dict[str, object]] = [{"$match": main_filter}]
    if event_name_filter is not None:
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "events",
                        "localField": "id",
                        "foreignField": "session_id",
                        "as": "events",
                    }
                },
                {
                    "$match": {
                        "$and": [
                            {"events": {"$ne": []}},
                            {"events.event_name": {"$in": event_name_filter}},
                            {"events.removed": {"$ne": True}},
                        ]
                    },
                },
            ]
        )
    pipeline += [
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
                        "sortBy": {"tasks.created_at": -1},
                    },
                }
            }
        },
        # Transform to get 1 doc = 1 task. We also add the task position.
        {"$unwind": {"path": "$tasks", "includeArrayIndex": "task_position"}},
        # Filter to keep only the last task (task_position = 0 ; starting from the end)
        {"$match": {"task_position": 0}},
        # Add a field "is_success" to the task
        {
            "$set": {
                "is_success": {"$cond": [{"$eq": ["$tasks.flag", "success"]}, 1, 0]}
            }
        },
        # Group on the task position
        {
            "$group": {
                "_id": 0,
                "count": {"$count": {}},
                "nb_success": {"$sum": "$is_success"},
                "success_rate": {"$avg": "$is_success"},
            }
        },
        {"$project": {"_id": 0, "success_rate": 1}},
    ]
    result = await mongo_db["sessions"].aggregate(pipeline).to_list(length=1)
    if len(result) == 0:
        return 0
    last_message_success_rate = result[0]["success_rate"]
    return last_message_success_rate


async def get_nb_sessions_per_day(
    project_id: str,
    start_timestamp: int,
    end_timestamp: int,
    event_name_filter: Optional[List[str]] = None,
) -> List[dict]:
    """
    Get the nb of sessions per day of a project.
    """
    mongo_db = await get_mongo_db()
    pipeline: List[Dict[str, object]] = [
        {
            "$match": {
                "project_id": project_id,
                "created_at": {"$gte": start_timestamp, "$lte": end_timestamp},
            }
        },
    ]
    if event_name_filter is not None:
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "events",
                        "localField": "id",
                        "foreignField": "session_id",
                        "as": "events",
                    }
                },
                {
                    "$match": {
                        "$and": [
                            {"events": {"$ne": []}},
                            {"events.event_name": {"$in": event_name_filter}},
                            {"events.removed": {"$ne": True}},
                        ]
                    },
                },
            ]
        )
    result = (
        await mongo_db["sessions"]
        .aggregate(
            pipeline
            + [
                {"$project": {"_id": 0, "created_at": 1}},
                {"$sort": {"date": 1}},
            ]
        )
        .to_list(length=None)
    )
    df = pd.DataFrame(result)
    complete_date_range = pd.date_range(
        datetime.datetime.fromtimestamp(start_timestamp, datetime.timezone.utc),
        datetime.datetime.fromtimestamp(end_timestamp, datetime.timezone.utc),
        freq="D",
    )
    complete_df = pd.DataFrame({"date": complete_date_range})
    complete_df["date"] = pd.to_datetime(complete_df["date"]).dt.date

    if not df.empty:
        df["date"] = pd.to_datetime(df["created_at"], unit="s", utc=True).dt.date
        # Group by date and count
        nb_sessions_per_day = (
            df.groupby(["date"])
            .count()
            .reset_index()[["date", "created_at"]]
            .rename(columns={"created_at": "nb_sessions"})
        )

        # Add missing days

        nb_sessions_per_day = pd.merge(
            complete_df, nb_sessions_per_day, on="date", how="left"
        ).fillna(0)
    else:
        nb_sessions_per_day = complete_df
        nb_sessions_per_day["nb_sessions"] = 0

    return nb_sessions_per_day[["date", "nb_sessions"]].to_dict(orient="records")


async def get_nb_sessions_histogram(
    project_id: str,
    event_name_filter: Optional[List[str]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
):
    """
    Get the number of sessions per session length
    """
    mongo_db = await get_mongo_db()
    main_filter: Dict[str, object] = {"project_id": project_id}
    if created_at_start is not None:
        main_filter["created_at"] = {"$gte": created_at_start}
    if created_at_end is not None:
        main_filter["created_at"] = {"$lte": created_at_end}
    pipeline: List[Dict[str, object]] = [{"$match": main_filter}]
    if event_name_filter is not None:
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "events",
                        "localField": "id",
                        "foreignField": "session_id",
                        "as": "events",
                    }
                },
                {
                    "$match": {
                        "$and": [
                            {"events": {"$ne": []}},
                            {"events.event_name": {"$in": event_name_filter}},
                            {"events.removed": {"$ne": True}},
                        ]
                    },
                },
            ]
        )
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
    event_name_filter: Optional[List[str]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
) -> Dict[str, object]:
    """
    Compute aggregated metrics for the sessions of a project. Used for the Sessions dashboard.
    """
    # TODO : Make the return keys parameters and optional (to avoid returning useless data)

    if await project_has_tasks(project_id) is False:
        return {}
    if await project_has_sessions(project_id) is False:
        return {}

    if metrics is None:
        metrics = [
            "total_nb_sessions",
            "average_session_length",
            "last_task_success_rate",
            "nb_sessions_per_day",
            "session_length_histogram",
            "success_rate_per_task_position",
        ]

    # Get timestamps
    today_datetime = datetime.datetime.now(datetime.timezone.utc)
    today_timestamp = int(today_datetime.timestamp())
    seven_days_ago_datetime = today_datetime - datetime.timedelta(days=6)
    # Round to the beginning of the day
    seven_days_ago_datetime = seven_days_ago_datetime.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    seven_days_ago_timestamp = int(seven_days_ago_datetime.timestamp())

    output: Dict[str, object] = {}

    if "total_nb_sessions" in metrics:
        output["total_nb_sessions"] = await get_total_nb_of_sessions(
            project_id=project_id,
            event_name_filter=event_name_filter,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
        )
    if "average_session_length" in metrics:
        output["average_session_length"] = await get_global_average_session_length(
            project_id=project_id,
            event_name_filter=event_name_filter,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
        )
    if "last_task_success_rate" in metrics:
        output["last_task_success_rate"] = await get_last_message_success_rate(
            project_id=project_id,
            event_name_filter=event_name_filter,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
        )
    if "nb_sessions_per_day" in metrics:
        output["nb_sessions_per_day"] = await get_nb_sessions_per_day(
            project_id=project_id,
            start_timestamp=seven_days_ago_timestamp,
            end_timestamp=today_timestamp,
            event_name_filter=event_name_filter,
        )
    if "session_length_histogram" in metrics:
        output["session_length_histogram"] = await get_nb_sessions_histogram(
            project_id=project_id,
            event_name_filter=event_name_filter,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
        )
    if "success_rate_per_task_position" in metrics:
        output[
            "success_rate_per_task_position"
        ] = await get_success_rate_per_task_position(
            project_id=project_id,
            quantile_filter=quantile_filter,
            event_name_filter=event_name_filter,
            created_at_start=created_at_start,
            created_at_end=created_at_end,
        )

    return output


async def create_ab_tests_table(project_id: str, limit: int = 1000) -> List[ABTest]:
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
                        "flag": {"$in": ["success", "failure"]},
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
                        "first_task_timestamp": {"$min": "$created_at"},
                        "score_std": {
                            "$stdDevSamp": {
                                "$cond": [{"$eq": ["$flag", "success"]}, 1, 0]
                            }
                        },
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "version_id": "$_id",
                        "score": 1,
                        "nb_tasks": 1,
                        "first_task_timestamp": 1,
                        "score_std": 1,
                    }
                },
                {"$sort": {"first_task_timestamp": -1}},
            ]
        )
        .to_list(length=limit)
    )
    # Validate models
    logger.debug(ab_tests)
    valid_ab_tests = []
    for ab_test in ab_tests:
        try:
            valid_ab_test = ABTest.model_validate(ab_test)
            valid_ab_tests.append(valid_ab_test)
        except pydantic.ValidationError:
            logger.debug(f"Skipping invalid ab_test: {ab_test}")

    return valid_ab_tests


async def fetch_topics(project_id: str, limit: int = 100) -> Topics:
    """
    Fetch the topics of a project
    """
    # Create an aggregated table
    mongo_db = await get_mongo_db()

    # Aggregation pipeline
    pipeline = [
        {"$match": {"project_id": project_id}},  # Filters documents by project_id
        {"$unwind": "$topics"},  # Deconstructs the topics array
        {
            "$group": {"_id": "$topics", "count": {"$sum": 1}}
        },  # Groups by topic and counts
        {
            "$project": {"topic_name": "$_id", "_id": 0, "count": 1}
        },  # Renames _id to topicName
        {"$sort": {"count": -1}},  # Sorts by count in descending order
    ]
    # Query Mongo
    topics = await mongo_db["tasks"].aggregate(pipeline).to_list(length=limit)

    return Topics(topics=topics)


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
) -> Dict[str, float]:
    """
    Get the success rate by event name of a project.
    """
    mongo_db = await get_mongo_db()
    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                "removed": {"$ne": True},
            }
        },
        {
            "$lookup": {
                "from": "tasks",
                "localField": "task_id",
                "foreignField": "id",
                "as": "tasks",
            }
        },
        {"$unwind": "$tasks"},
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


async def get_events_aggregated_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
) -> Dict[str, object]:
    if metrics is None:
        metrics = [
            "success_rate_by_event_name",
        ]
    output: Dict[str, object] = {}
    if "success_rate_by_event_name" in metrics:
        output["success_rate_by_event_name"] = await get_success_rate_by_event_name(
            project_id=project_id,
        )
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
    limit: int = 1000,
    with_events: bool = True,
    with_sessions: bool = True,
) -> List[FlattenedTask]:
    """
    Get a flattened representation of the tasks of a project for analytics
    """
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
    }
    if with_events:
        pipeline.extend(
            [
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
        return_columns = {
            **return_columns,
            "event_name": "$event_name",
            "event_created_at": "$event_created_at",
        }
    if with_sessions:
        await compute_session_length(project_id)
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

    pipeline.extend(
        [
            {"$project": return_columns},
            {"$sort": {"task_created_at": -1}},
        ]
    )
    # Query Mongo
    flattened_tasks = await mongo_db["tasks"].aggregate(pipeline).to_list(length=limit)
    # Ignore _id field
    flattened_tasks = [
        {k: v for k, v in task.items() if k != "_id"} for task in flattened_tasks
    ]
    # Cast
    flattened_tasks = [FlattenedTask.model_validate(task) for task in flattened_tasks]

    return flattened_tasks


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

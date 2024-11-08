from typing import Dict, List, Optional

from app.api.platform.models import Pagination, Sorting
from app.api.v2.models.projects import UserMetadata
from app.db.mongo import get_mongo_db
from app.services.mongo.query_builder import QueryBuilder
import datetime as dt
from typing import cast, Union
from collections import defaultdict
from loguru import logger

from phospho.models import ProjectDataFilters


async def fetch_users_metadata(
    project_id: str,
    filters: ProjectDataFilters,
    sorting: Optional[List[Sorting]] = None,
    pagination: Optional[Pagination] = None,
    user_id_search: Optional[str] = None,
) -> List[UserMetadata]:
    """
    Get the user metadata.

    - project_id: str
    - filters: ProjectDataFilters
    - sorting: Optional[List[Sorting]]
    - pagination: Optional[Pagination]
    - user_id_search: Optional[str] Search for a specific user_id.
        It uses a regex to match the user_id, so it can be a partial match.

    The UserMetadata contains:
        user_id: str
        nb_tasks: int
        avg_success_rate: float
        avg_session_length: float
        nb_tokens: int
        events: List[Event]
        tasks_id: List[str]
        session_ids: List[str]
        first_message_ts: datetime
        last_message_ts: datetime
    """

    mongo_db = await get_mongo_db()
    # To keep track of the fields that are computed and need to be carried over
    all_computed_fields = []

    # Only fetch tasks with user_id
    if filters.metadata is None:
        filters.metadata = {}
    if filters.user_id is None and filters.metadata.get("user_id") is None:
        filters.metadata["user_id"] = {"$ne": None}
    if user_id_search:
        filters.metadata["user_id"] = {"$regex": user_id_search}

    query_builder = QueryBuilder(
        project_id=project_id, filters=filters, fetch_objects="tasks"
    )

    pipeline = await query_builder.build()

    # Compute
    pipeline += [
        {
            "$set": {
                "is_success": {
                    "$cond": [{"$eq": ["$human_eval.flag", "success"]}, 1, 0]
                },
                # If metadata.total_tokens is not present, set to 0
                "metadata.total_tokens": {
                    "$cond": [
                        {"$eq": [{"$type": "$metadata.total_tokens"}, "missing"]},
                        0,
                        "$metadata.total_tokens",
                    ]
                },
            }
        },
        {
            "$group": {
                "_id": "$metadata.user_id",
                "nb_tasks": {"$sum": 1},
                "avg_success_rate": {"$avg": {"$toInt": "$is_success"}},
                "total_tokens": {"$sum": "$metadata.total_tokens"},
                "task_ids": {"$addToSet": "$id"},
                "session_ids": {"$addToSet": "$session_id"},
                # First and last message timestamp
                "first_message_ts": {"$min": "$created_at"},
                "last_message_ts": {"$max": "$created_at"},
            }
        },
    ]

    all_computed_fields.extend(
        [
            "nb_tasks",
            "avg_success_rate",
            "total_tokens",
            "task_ids",
            "first_message_ts",
            "last_message_ts",
            "session_ids",
        ]
    )

    # Override the created_at filters to filter by last_message_ts
    filter_last_message_ts_start = filters.created_at_start
    filter_last_message_ts_end = filters.created_at_end
    secondary_filter: Dict[str, object] = {}
    if filter_last_message_ts_start is not None:
        secondary_filter["last_message_ts"] = {"$gte": filter_last_message_ts_start}
    if filter_last_message_ts_end is not None:
        secondary_filter["last_message_ts"] = {
            **secondary_filter.get("last_message_ts", {}),  # type: ignore
            "$lte": filter_last_message_ts_end,
        }
    if secondary_filter:
        pipeline += [{"$match": secondary_filter}]

    # Apply the sorting
    if sorting:
        logger.info(f"Sorting by: {sorting}")
        sort_dict = {sort.id: 1 if sort.desc else -1 for sort in sorting}
        # Rename the id user_id by _id
        sort_dict["_id"] = sort_dict.pop("user_id", 1)
        pipeline += [{"$sort": sort_dict}]
    else:
        pipeline += [{"$sort": {"last_message_ts": 1, "_id": -1}}]

    # Adds the pagination
    # TODO: All the steps above are pretty slow. Server-side pagination does not work well with this approach.
    # We should create a new collection to persist the user metadata and use it for pagination, like Sessions.
    if pagination:
        pipeline += [
            {"$skip": pagination.page * pagination.per_page},
            {"$limit": pagination.per_page},
        ]

    # Adds the list of unique detected events.
    # This is a bit tricky because we need to deduplicate the events based on the event_definition.id
    # For now, we only keep the first event with the same event_definition.id
    pipeline += [
        {"$unwind": "$task_ids"},
        {
            "$lookup": {
                "from": "events",
                "localField": "task_ids",
                "foreignField": "task_id",
                "as": "events",
            }
        },
        {
            "$unwind": {
                "path": "$events",
                "preserveNullAndEmptyArrays": True,
            }
        },
        # (Optional) Keep only tagger events
        # {
        #     "$match": {
        #         "events.event_definition.score_range_settings.score_type": "confidence"
        #     }
        # },
        {
            "$set": {
                "events.def_id_cat": {
                    "$cond": [
                        {
                            "$eq": [
                                "$events.event_definition.score_range_settings.score_type",
                                "category",
                            ]
                        },
                        {
                            "$concat": [
                                "$events.event_definition.id",
                                "$events.score_range.label",
                            ]
                        },
                        "$events.event_definition.id",
                    ]
                }
            }
        },
        # Deduplicate the events based on the event.event_definition.id
        {
            "$group": {
                "_id": {"user_id": "$_id", "event_id": "$events.def_id_cat"},
                "events": {"$push": "$events"},
                **{field: {"$first": f"${field}"} for field in all_computed_fields},
            }
        },
        # Ajouter une disjonction de cas pour les events non taggers
        {
            "$set": {
                "events.count": {"$size": "$events"},
                "events.avg_score": {"$avg": "$events.score_range.value"},
            }
        },
        {
            "$set": {
                "events": {"$first": "$events"},
            }
        },
        # Group by user_id
        # Add here one field
        {
            "$group": {
                "_id": "$_id.user_id",
                "events": {"$push": "$events"},
                **{field: {"$first": f"${field}"} for field in all_computed_fields},
            }
        },
        # Filter the events to only keep non-null values
        {
            "$set": {
                "events": {
                    "$filter": {
                        "input": "$events",
                        "as": "event",
                        "cond": {"$ne": ["$$event", None]},
                    }
                }
            }
        },
    ]

    query_builder.deduplicate_tasks_events()
    all_computed_fields.append("events")

    # Compute the average session length
    pipeline += [
        {
            "$unwind": "$session_ids",
        },
        {
            "$lookup": {
                "from": "sessions",
                "localField": "session_ids",
                "foreignField": "id",
                "as": "session",
            }
        },
        {"$unwind": "$session"},
        # Compute the average session length and carry over the other fields
        {
            "$group": {
                "_id": "$_id",
                "avg_session_length": {"$avg": "$session.session_length"},
                **{field: {"$first": f"${field}"} for field in all_computed_fields},
            }
        },
    ]
    all_computed_fields.append("avg_session_length")

    # Project the fields we want to keep and rename the _id to user_id
    pipeline += [
        {
            "$project": {
                "user_id": "$_id",
                **{field: 1 for field in all_computed_fields},
            }
        },
    ]

    logger.debug(f"{pipeline}")

    # group made us lose the order. We need to sort again
    if sorting:
        logger.info(f"Sorting by: {sorting}")
        sort_dict = {sort.id: 1 if sort.desc else -1 for sort in sorting}
        # Rename the id user_id by _id
        sort_dict["_id"] = sort_dict.pop("user_id", 1)
        pipeline += [{"$sort": sort_dict}]
    else:
        pipeline += [{"$sort": {"last_message_ts": 1, "_id": -1}}]

    users = (
        await mongo_db["tasks"]
        .aggregate(pipeline, allowDiskUse=True)
        .to_list(length=None)
    )
    if users is None or (filters.user_id is not None and len(users) == 0):
        return []

    users = [UserMetadata.model_validate(data) for data in users if data.get("user_id")]

    return users


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


async def get_user_retention(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
) -> Optional[List[Dict[str, Union[str, float]]]]:
    mongo_db = await get_mongo_db()

    if filters is None:
        filters = ProjectDataFilters()

    if filters.created_at_end is None:
        # Set created_at_end to the current time
        filters.created_at_end = int(dt.datetime.now().timestamp())
    if filters.created_at_start is None:
        # Set created_at_start to 12 weeks before created_at_end
        if isinstance(filters.created_at_end, int):
            filters.created_at_start = filters.created_at_end - 12 * 7 * 86400
        elif isinstance(filters.created_at_end, dt.datetime):
            filters.created_at_start = filters.created_at_end - dt.timedelta(weeks=12)
        else:
            raise ValueError("created_at_end should be an int or a datetime")

    if isinstance(filters.created_at_start, dt.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, dt.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    time_diff = cast(int, filters.created_at_end) - cast(int, filters.created_at_start)
    number_of_weeks = int(time_diff / (7 * 86400))

    use_daily = (
        number_of_weeks < 2
    )  # If the period is less than 2 weeks, we use daily retention

    period_length = int(time_diff / 86400) if use_daily else number_of_weeks
    period_seconds = (
        86400 if use_daily else 86400 * 7
    )  # 86400 seconds in a day, 86400 * 7 seconds in a week
    period_name = "day" if use_daily else "week"

    query_builder = QueryBuilder(
        project_id=project_id, filters=filters, fetch_objects="tasks"
    )
    # The query builder will fetch the tasks with the correct project_id and filters
    pipeline = await query_builder.build()

    # We need to filter tasks with metadata.user_id
    # We then want to determine the users present in the first period
    # And the percentage of them still present at subsequent periods until the end
    pipeline += [
        # Find all tasks with user IDs
        {"$match": {"metadata.user_id": {"$exists": True, "$ne": None}}},
        # Group by user to get their timestamps
        {
            "$group": {
                "_id": "$metadata.user_id",
                "first_seen": {"$min": "$created_at"},
                "last_seen": {"$max": "$created_at"},
            }
        },
    ]

    user_activities = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)

    if not user_activities:
        return None

    return calculate_retention(
        user_activities=user_activities,
        period_length=period_length,
        period_seconds=period_seconds,
        period_name=period_name,
    )


def calculate_retention(
    user_activities: List[Dict[str, int]],
    period_length: int,
    period_seconds: int,
    period_name: str,
) -> List[dict]:
    """
    Calculate retention metrics from raw user activity data.

    Args:
        user_activities: List of dicts containing first_seen and last_seen timestamps for each user
        period_length: Maximum number of periods to analyze
        period_seconds: Number of seconds in each period (daily or weekly)
        period_name: Name of the period type ("day" or "week")
    """
    if not user_activities:
        return []

    # Find the start of our analysis period
    min_timestamp = min(user["first_seen"] for user in user_activities)
    max_timestamp = max(user["last_seen"] for user in user_activities)

    # Calculate actual number of periods in our data
    actual_periods = min(
        period_length, int((max_timestamp - min_timestamp) / period_seconds)
    )

    # Count users active in each period
    total_users = len(user_activities)
    period_dropoffs: Dict[int, int] = defaultdict(int)

    # Calculate which period each user dropped off
    for user in user_activities:
        periods_active = int((user["last_seen"] - user["first_seen"]) / period_seconds)
        period_dropoffs[periods_active] += 1

    # Calculate retention for each period
    retention = []
    active_users = total_users

    for period in range(actual_periods + 1):
        # Calculate the date for this period
        period_date = min_timestamp + (period * period_seconds)

        retention.append(
            {
                period_name: period,
                "retention": round((active_users / total_users) * 100, 1),
                "date": period_date,  # Add the timestamp for this period
            }
        )

        # Subtract users who didn't continue to next period
        if period in period_dropoffs:
            active_users -= period_dropoffs[period]

    return retention


async def get_average_nb_tasks_per_user(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
) -> Optional[float]:
    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id, filters=filters, fetch_objects="tasks"
    )
    pipeline = await query_builder.build()

    pipeline += [
        {
            "$match": {
                "metadata.user_id": {"$exists": True},
            }
        },
        {"$group": {"_id": "$metadata.user_id", "count": {"$sum": 1}}},
        {"$group": {"_id": None, "average": {"$avg": "$count"}}},
    ]

    result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)
    if not result or "average" not in result[0]:
        return None
    average = result[0]["average"]
    return average


async def get_users_aggregated_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
):
    if metrics is None:
        metrics = []

    output: Dict[str, object] = {}
    if "nb_users" in metrics:
        total_nb_users = (
            await get_total_nb_of_users(
                project_id=project_id,
                filters=filters,
            )
            # If None, set to 0
            or 0
        )
        output["nb_users"] = total_nb_users

    if "avg_nb_tasks_per_user" in metrics:
        output["avg_nb_tasks_per_user"] = await get_average_nb_tasks_per_user(
            project_id=project_id, filters=filters
        )

    if "nb_users_messages" in metrics:
        # Number of messages sent by users
        output["nb_users_messages"] = await get_nb_users_messages(
            project_id=project_id,
            filters=filters,
        )

    if "user_retention" in metrics:
        # User retention
        output["user_retention"] = await get_user_retention(
            project_id=project_id,
            filters=filters,
        )

    return output

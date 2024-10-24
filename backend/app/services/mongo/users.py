from typing import Dict, List, Optional

from app.api.platform.models import Pagination, Sorting
from app.api.v2.models.projects import UserMetadata
from app.db.mongo import get_mongo_db
from app.services.mongo.query_builder import QueryBuilder
import datetime as dt
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
        # Deduplicate the events based on the event.event_definition.id
        {
            "$group": {
                "_id": {
                    "user_id": "$_id",
                    "event_id": "$events.event_definition.id",
                },
                "events": {"$first": "$events"},
                **{field: {"$first": f"${field}"} for field in all_computed_fields},
            }
        },
        # Group by user_id
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

    users = [UserMetadata.model_validate(data) for data in users]

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
    filters: Optional[ProjectDataFilters] = ProjectDataFilters(),
) -> Optional[Dict[str, int]]:
    mongo_db = await get_mongo_db()

    if filters.created_at_end is None:
        # Set created_at_end to the current time
        filters.created_at_end = int(dt.datetime.now().timestamp())
    if filters.created_at_start is None:
        # Set created_at_start to 12 weeks before created_at_end
        filters.created_at_start = filters.created_at_end - 12 * 7 * 86400

    time_diff = filters.created_at_end - filters.created_at_start
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
        {"$match": {"metadata.user_id": {"$exists": True, "$ne": None}}},
        # Group by user to get their first and last interaction timestamps
        {
            "$group": {
                "_id": "$metadata.user_id",
                "first_seen": {"$min": "$created_at"},
                "last_seen": {"$max": "$created_at"},
            }
        },
        # Calculate period number for first and last seen
        {
            "$addFields": {
                "first_period": {
                    "$floor": {
                        "$divide": [
                            {
                                "$subtract": ["$first_seen", "$first_seen"]
                            },  # This will start from period 0
                            period_seconds,
                        ]
                    }
                },
                "last_period": {
                    "$floor": {
                        "$divide": [
                            {"$subtract": ["$last_seen", "$first_seen"]},
                            period_seconds,
                        ]
                    }
                },
            }
        },
        # Group all users by their first period, this gives us the cohorts
        {
            "$group": {
                "_id": "$first_period",
                "total_users": {"$sum": 1},
                "users_by_last_period": {"$push": "$last_period"},
            }
        },
        # Only consider the first cohort (period 0)
        {"$match": {"_id": 0}},
        # Unwind the last period array to count users present in each period
        {
            "$project": {
                "total_users": 1,
                "retention_by_period": {
                    "$map": {
                        "input": {
                            "$range": [
                                0,
                                period_length + 1,
                            ]
                        },
                        "as": "period",
                        "in": {
                            "period": "$$period",
                            "count": {
                                "$size": {
                                    "$filter": {
                                        "input": "$users_by_last_period",
                                        "as": "last_period",
                                        "cond": {"$gte": ["$$last_period", "$$period"]},
                                    }
                                }
                            },
                        },
                    }
                },
            }
        },
    ]

    result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)

    if not result or not result[0]["total_users"]:
        return None

    # Calculate retention percentages
    first_cohort = result[0]
    total_users = first_cohort["total_users"]

    retention = []
    for period_data in first_cohort["retention_by_period"]:
        retention.append(
            {
                period_name: period_data["period"],
                "retention": round((period_data["count"] / total_users) * 100, 1),
            }
        )

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

from typing import Dict, List, Literal

from app.api.platform.models.metadata import MetadataPivotQuery
from app.core import constants
from app.db.mongo import get_mongo_db
from app.services.mongo.query_builder import QueryBuilder
from app.services.mongo.sessions import compute_session_length, compute_task_position
from fastapi import HTTPException
from loguru import logger


async def _build_unique_metadata_fields_pipeline(
    project_id: str, type: Literal["number", "string"] = "number"
) -> List[Dict[str, object]]:
    pipeline: List[Dict[str, object]] = [
        {
            "$match": {
                "project_id": project_id,
                "$and": [
                    {"metadata": {"$exists": True}},
                    {"metadata": {"$ne": {}}},
                ],
            },
        },
        {
            "$project": {"metadata_keys": {"$objectToArray": "$metadata"}},
        },
        {"$unwind": "$metadata_keys"},
    ]
    # Filter by type
    # https://www.mongodb.com/docs/manual/reference/operator/query/type/
    if type == "number":
        pipeline.append(
            {
                "$match": {
                    "$expr": {"$eq": [{"$isNumber": "$metadata_keys.v"}, True]},
                }
            }
        )
    if type == "string":
        pipeline.append(
            {
                "$match": {
                    "$expr": {"$eq": [{"$type": "$metadata_keys.v"}, "string"]},
                }
            }
        )

    return pipeline


async def collect_unique_metadata_fields(
    project_id: str,
    type: Literal["number", "string"] = "number",
) -> List[str]:
    """
    Get the unique metadata keys for a project
    """
    mongo_db = await get_mongo_db()
    pipeline = await _build_unique_metadata_fields_pipeline(project_id, type)
    pipeline += [
        {
            "$group": {
                "_id": None,
                "metadata_keys": {
                    "$addToSet": "$metadata_keys.k",
                },
                "count": {"$sum": 1},
            },
        },
        {"$sort": {"count": -1, "metadata_keys": 1}},
    ]

    keys = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)
    if not keys or len(keys) == 0 or "metadata_keys" not in keys[0]:
        # No metadata keys found
        return []
    keys = keys[0]["metadata_keys"]
    return keys


async def collect_unique_metadata_field_values(
    project_id: str, type: Literal["number", "string"] = "string"
) -> Dict[str, List[str]]:
    """
    Get the unique metadata values for all the metadata fields of a certain
    type in a project.
    """
    if type not in ["string"]:
        raise NotImplementedError("Only string metadata values are supported")

    mongo_db = await get_mongo_db()
    pipeline = await _build_unique_metadata_fields_pipeline(project_id, type)

    # Extend the pipeline to create a dict: metadata_key: [metadata_values]
    pipeline += [
        {
            "$match": {
                "metadata_keys.k": {"$ne": "task_id"},
            }
        },
        {
            "$group": {
                "_id": "$metadata_keys.k",
                "metadata_values": {
                    "$addToSet": "$metadata_keys.v",
                },
                # "count": {"$sum": 1},
            },
        },
        {
            "$project": {
                "metadata_key": "$_id",
                "metadata_values": 1,
            }
        },
        {
            "$sort": {"metadata_key": 1, "metadata_values": 1},
        },
    ]
    keys_and_values = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)
    if not keys_and_values or len(keys_and_values) == 0:
        return {}
    keys_to_values = {
        key["metadata_key"]: key["metadata_values"] for key in keys_and_values
    }

    return keys_to_values


async def breakdown_by_sum_of_metadata_field(
    project_id: str,
    pivot_query: MetadataPivotQuery,
):
    """
    Get the sum of a metadata field, grouped by another metadata field if provided.

    The metric can be one of the following:
    - "count_unique": Number of unique values of the metadata field
    - "sum": Sum of the metadata field
    - "avg": Average of the metadata field
    - "nb_messages": Number of tasks
    - "nb_sessions": Number of sessions
    - "tags_count": Number of detected tags
    - "tags_distribution": Distribution of detected tags
    - "avg_scorer_value": Average scorer value
    - "avg_success_rate": Average human rating
    - "avg_session_length": Average session length

    The breakdown_by field can be one of the following:
    - A metadata field
    - A time field: day, week, month
    - "tagger_name"
    - "task_position"
    - "None"
    - "session_length"

    scorer_id is only used when metric is "avg_scorer_value", it tells us which scorer to use.

    The output is a list of dictionaries, each containing:
    - breakdown_by: str
    - metric: float
    - stack: Dict[str, float] (only for "tags_distribution") containing the event_name and its count

    The output stack can be used to create a stacked bar chart.
    """

    metric = pivot_query.metric
    metadata_field = pivot_query.metric_metadata
    breakdown_by = pivot_query.breakdown_by
    breakdown_by_event_id = pivot_query.breakdown_by_event_id
    scorer_id = pivot_query.scorer_id
    filters = pivot_query.filters

    logger.info(f"Running pivot with:\n{pivot_query.model_dump()}")

    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="tasks",
        filters=pivot_query.filters,
    )
    pipeline = await query_builder.build()

    def _merge_sessions(pipeline: List[Dict[str, object]]) -> None:
        # if already merged, return the pipeline
        if any(
            operator.get("$lookup", {}).get("from") == "sessions"  # type: ignore
            for operator in pipeline
        ):
            return

        # Merge the sessions with the tasks
        pipeline += [
            {
                "$lookup": {
                    "from": "sessions",
                    "localField": "session_id",
                    "foreignField": "id",
                    "as": "session",
                },
            },
            {
                "$addFields": {
                    "session": {"$ifNull": ["$session", []]},
                }
            },
            {
                "$unwind": "$session",
            },
            {
                "$set": {
                    "session_length": "$session.session_length",
                }
            },
        ]

    def _unwind_events(pipeline: List[Dict[str, object]]) -> None:
        # Unwind the events array if not already done
        if any(operator.get("$unwind") == "$events" for operator in pipeline):
            return

        pipeline += [
            {"$unwind": "$events"},
        ]

    category_metadata_fields = constants.RESERVED_CATEGORY_METADATA_FIELDS
    number_metadata_fields = constants.RESERVED_NUMBER_METADATA_FIELDS

    if metadata_field is not None:
        # Beware, these lists contains duplicate values
        # This is ok for now
        category_metadata_fields = (
            category_metadata_fields
            + await collect_unique_metadata_fields(project_id=project_id, type="string")
        )
        number_metadata_fields = (
            number_metadata_fields
            + await collect_unique_metadata_fields(project_id=project_id, type="number")
        )

    logger.debug(f"Category metadata fields: {category_metadata_fields}")
    logger.debug(f"Number metadata fields: {number_metadata_fields}")

    if breakdown_by in category_metadata_fields:
        breakdown_by_col = f"metadata.{breakdown_by}"
    elif breakdown_by == "None":
        breakdown_by_col = "id"
    elif breakdown_by in ["day", "week", "month"]:
        breakdown_by_col = "time_period"
        # We cant to group our data by day, week or month
        pipeline += [
            {
                "$addFields": {
                    "time_period": {
                        "$dateToString": {
                            "date": {
                                "$toDate": {
                                    "$convert": {
                                        # Multiply by 1000 to convert to milliseconds
                                        "input": {"$multiply": ["$created_at", 1000]},
                                        "to": "long",
                                    }
                                }
                            },
                            "format": "%Y-%m-%d"
                            if breakdown_by == "day"
                            else "%Y-%U"
                            if breakdown_by == "week"
                            else "%Y-%B",
                        }
                    }
                }
            }
        ]
    elif breakdown_by == "session_length":
        await compute_session_length(project_id=project_id)
        _merge_sessions(pipeline)
        breakdown_by_col = "session_length"
    elif breakdown_by is None:
        breakdown_by_col = None
    else:
        breakdown_by_col = breakdown_by

    if breakdown_by == "tagger_name":
        query_builder.merge_events(foreignField="task_id")
        pipeline += [
            # Filter to only keep the tagger events
            {
                "$match": {
                    "events": {"$exists": True, "$ne": []},
                    "events.event_definition.score_range_settings.score_type": "confidence",
                }
            },
            {
                "$set": {
                    "taggers": {
                        "$filter": {
                            "input": "$events",
                            "as": "event",
                            "cond": {
                                "$eq": [
                                    "$$event.event_definition.score_range_settings.score_type",
                                    "confidence",
                                ]
                            },
                        }
                    }
                }
            },
            {"$unwind": "$taggers"},
            {"$set": {"tagger_name": "$taggers.event_definition.event_name"}},
        ]
        breakdown_by_col = "tagger_name"
    elif breakdown_by == "scorer_value":
        query_builder.merge_events(foreignField="task_id")
        pipeline += [
            {
                "$match": {
                    "events": {"$exists": True, "$ne": []},
                    "events.event_definition.score_range_settings.score_type": "range",
                    "events.event_definition.id": breakdown_by_event_id,
                },
            },
            # Filter the $events array to only keep the event with the breakdown_by_event_id
            {
                "$set": {
                    "scorer": {
                        "$first": {
                            "$filter": {
                                "input": "$events",
                                "as": "event",
                                "cond": {
                                    "$and": [
                                        {
                                            "$eq": [
                                                "$$event.event_definition.id",
                                                breakdown_by_event_id,
                                            ]
                                        }
                                    ]
                                },
                            }
                        },
                    }
                }
            },
            {
                "$set": {
                    "scorer_value_label": {
                        # Round the scorer value to the nearest integer
                        "$round": "$scorer.score_range.value"
                    }
                }
            },
        ]
        breakdown_by_col = "scorer_value_label"
    elif breakdown_by == "classifier_value":
        query_builder.merge_events(foreignField="task_id")
        pipeline += [
            {
                "$match": {
                    "events": {"$exists": True, "$ne": []},
                    "events.event_definition.score_range_settings.score_type": "category",
                    "events.event_definition.id": breakdown_by_event_id,
                },
            },
            {
                "$set": {
                    "classifier": {
                        "$first": {
                            "$filter": {
                                "input": "$events",
                                "as": "event",
                                "cond": {
                                    "$and": [
                                        {
                                            "$eq": [
                                                "$$event.event_definition.id",
                                                breakdown_by_event_id,
                                            ]
                                        }
                                    ]
                                },
                            }
                        }
                    }
                }
            },
            {"$set": {"classifier_label": "$classifier.score_range.label"}},
        ]
        breakdown_by_col = "classifier_label"

    if breakdown_by == "task_position":
        await compute_task_position(project_id=project_id, filters=filters)
        breakdown_by_col = "task_position"

    if metric == "nb_messages":
        pipeline += [
            {
                "$group": {
                    "_id": f"${breakdown_by_col}",
                    "metric": {"$sum": 1},
                },
            },
            {
                "$project": {
                    "breakdown_by": "$_id",
                    "metric": 1,
                }
            },
        ]

    if metric == "nb_sessions":
        # Count the number of unique sessions and group by breakdown_by
        pipeline += [
            {
                "$group": {
                    "_id": f"${breakdown_by_col}",
                    "metric": {"$addToSet": "$session_id"},
                },
            },
            {
                "$project": {
                    "breakdown_by": "$_id",
                    "metric": {"$size": "$metric"},
                }
            },
        ]

    if metric == "avg_success_rate":
        pipeline += [
            {
                "$match": {
                    "flag": {"$exists": True},
                }
            },
            {"$set": {"is_success": {"$cond": [{"$eq": ["$flag", "success"]}, 1, 0]}}},
            {
                "$group": {
                    "_id": f"${breakdown_by_col}",
                    "metric": {"$avg": "$is_success"},
                },
            },
            {
                "$project": {
                    "breakdown_by": "$_id",
                    "metric": 1,
                }
            },
        ]

    if metric == "avg_scorer_value":
        query_builder.merge_events(foreignField="task_id")
        _unwind_events(pipeline)
        pipeline += [
            # Filter to only keep the scorer events
            {
                "$match": {
                    "events.event_definition.id": scorer_id,
                }
            },
        ]

        pipeline += [
            {
                "$group": {
                    "_id": f"${breakdown_by_col}",
                    "metric": {"$avg": "$events.score_range.value"},
                },
            },
            {
                "$project": {
                    "breakdown_by": "$_id",
                    "metric": 1,
                }
            },
        ]

    if metric == "avg_session_length":
        _merge_sessions(pipeline)
        pipeline += [
            {
                "$group": {
                    "_id": f"${breakdown_by_col}",
                    "metric": {"$avg": "$session.session_length"},
                },
            },
            {
                "$project": {
                    "breakdown_by": "$_id",
                    "metric": 1,
                }
            },
        ]

    if metric == "tags_count" or metric == "tags_distribution":
        # Count the number of events for each event_name
        query_builder.merge_events(foreignField="task_id")
        _unwind_events(pipeline)
        pipeline += [
            {
                "$group": {
                    "_id": {
                        "breakdown_by": f"${breakdown_by_col}",
                        "event_name": "$events.event_name",
                    },
                    "metric": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$events.event_definition.score_range_settings.score_type",
                                        "confidence",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                },
            },
            {
                "$group": {
                    "_id": "$_id.breakdown_by",
                    "events": {
                        "$push": {"event_name": "$_id.event_name", "metric": "$metric"}
                    },
                    "total": {"$sum": "$metric"},
                }
            },
            # Filter out the events with a metric of 0
            {
                "$set": {
                    "events": {
                        "$filter": {
                            "input": "$events",
                            "as": "event",
                            "cond": {"$ne": ["$$event.metric", 0]},
                        }
                    }
                }
            },
        ]

        if metric == "tags_count":
            pipeline += [
                {
                    "$project": {
                        "_id": 0,
                        "breakdown_by": "$_id",
                        "stack": {
                            "$arrayToObject": {
                                "$map": {
                                    "input": "$events",
                                    "as": "event",
                                    "in": {
                                        "k": "$$event.event_name",
                                        "v": "$$event.metric",
                                    },
                                }
                            }
                        },
                    }
                },
                {"$unwind": "$stack"},
            ]
        if metric == "tags_distribution":
            # Same as tags_count, but normalize the count by the total number of events for each breakdown_by
            pipeline += [
                {
                    "$project": {
                        "_id": 0,
                        "breakdown_by": "$_id",
                        "stack": {
                            "$arrayToObject": {
                                "$map": {
                                    "input": "$events",
                                    "as": "event",
                                    "in": {
                                        "k": "$$event.event_name",
                                        "v": {"$divide": ["$$event.metric", "$total"]},
                                    },
                                }
                            }
                        },
                    }
                },
                {"$unwind": "$stack"},
            ]

    if metric == "sum":
        if metadata_field in number_metadata_fields:
            pipeline += [
                {
                    "$match": {
                        f"metadata.{metadata_field}": {"$exists": True},
                    }
                },
                {
                    "$group": {
                        "_id": f"${breakdown_by_col}",
                        "metric": {
                            "$sum": f"$metadata.{metadata_field}",
                        },
                    },
                },
                {
                    "$project": {
                        "breakdown_by": "$_id",
                        "metric": 1,
                    }
                },
            ]
        else:
            logger.error(
                f"Metric 'sum' is only supported for number metadata fields. Provided metadata field: {metadata_field}"
            )
            raise HTTPException(
                status_code=400,
                detail="Metric 'sum' is only supported for number metadata fields",
            )
    if metric == "avg":
        if metadata_field in number_metadata_fields:
            pipeline += [
                {
                    "$match": {
                        f"metadata.{metadata_field}": {"$exists": True},
                    }
                },
                {
                    "$group": {
                        "_id": f"${breakdown_by_col}",
                        "metric": {"$avg": f"$metadata.{metadata_field}"},
                    },
                },
                {
                    "$project": {
                        "breakdown_by": "$_id",
                        "metric": 1,
                    }
                },
            ]
        else:
            logger.error(
                f"Metric 'avg' is only supported for number metadata fields. Provided metadata field: {metadata_field}"
            )
            raise HTTPException(
                status_code=400,
                detail="Metric 'avg' is only supported for number metadata fields",
            )

    if metric == "count_unique":
        if metadata_field in category_metadata_fields:
            pipeline += [
                {
                    "$group": {
                        "_id": f"${breakdown_by_col}",
                        "metric": {
                            "$addToSet": f"$metadata.{metadata_field}",
                        },
                    },
                },
                {
                    "$project": {
                        "breakdown_by": "$_id",
                        "metric": {"$size": "$metric"},
                    }
                },
            ]
        else:
            logger.error(
                f"Metric 'count_unique' is only supported for category metadata fields. Provided metadata field: {metadata_field}"
            )
            raise HTTPException(
                status_code=400,
                detail="Metric 'count_unique' is only supported for category metadata fields",
            )

    # Sort
    pipeline.append({"$sort": {"breakdown_by": 1, "metric": 1}})
    # Select only the relevant fields
    pipeline.append(
        {
            "$project": {
                "_id": 0,
            }
        }
    )

    if breakdown_by in ["classifier_value", "scorer_value"]:
        # Filter the None breadkown_by values
        pipeline.append(
            {
                "$match": {
                    "breakdown_by": {"$ne": None},
                }
            }
        )

    logger.info(f"Pivot pipeline:\n {pipeline}")

    result = await mongo_db["tasks"].aggregate(pipeline).to_list(length=200)

    return result

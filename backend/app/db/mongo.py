import pymongo
from loguru import logger

from app.core.config import (
    MONGODB_MAXPOOLSIZE,
    MONGODB_MINPOOLSIZE,
    MONGODB_NAME,
    MONGODB_URL,
)
from motor.motor_asyncio import AsyncIOMotorClient

mongo_db = None


async def get_mongo_db():
    if mongo_db is None:
        raise Exception("Mongo is not initialized.")
    return mongo_db[MONGODB_NAME]


async def connect_and_init_db():
    global mongo_db
    try:
        if MONGODB_URL is None:
            logger.warning("MONGODB_URL is None. Skipping mongo connection.")
            return
        try:
            mongo_db = AsyncIOMotorClient(
                MONGODB_URL,
                maxPoolSize=MONGODB_MAXPOOLSIZE,
                minPoolSize=MONGODB_MINPOOLSIZE,
                uuidRepresentation="standard",
            )
            logger.info(f"Connected to mongodb (MONGODB_NAME={MONGODB_NAME})")

            # Create indexes
            # https://motor.readthedocs.io/en/stable/api-tornado/motor_collection.html#motor.motor_tornado.MotorCollection.create_index
            # Projects
            mongo_db[MONGODB_NAME]["projects"].create_index(
                "id", unique=True, background=True
            )
            mongo_db[MONGODB_NAME]["projects"].create_index("org_id", background=True)

            # Sessions
            mongo_db[MONGODB_NAME]["sessions"].create_index(
                "id", unique=True, background=True
            )
            mongo_db[MONGODB_NAME]["sessions"].create_index(
                "project_id", background=True
            )
            mongo_db[MONGODB_NAME]["sessions"].create_index(
                [("created_at", pymongo.DESCENDING)], background=True
            )
            mongo_db[MONGODB_NAME]["sessions"].create_index(
                ["project_id", ("created_at", pymongo.DESCENDING)], background=True
            )

            # Tasks
            mongo_db[MONGODB_NAME]["tasks"].create_index(
                "id", unique=True, background=True
            )
            mongo_db[MONGODB_NAME]["tasks"].create_index("org_id", background=True)
            mongo_db[MONGODB_NAME]["tasks"].create_index("session_id", background=True)
            mongo_db[MONGODB_NAME]["tasks"].create_index("test_id", background=True)
            mongo_db[MONGODB_NAME]["tasks"].create_index(
                [("created_at", pymongo.DESCENDING)], background=True
            )
            mongo_db[MONGODB_NAME]["tasks"].create_index(
                [("created_at", pymongo.ASCENDING)], background=True
            )
            mongo_db[MONGODB_NAME]["tasks"].create_index(
                ["project_id", "test_id", ("created_at", pymongo.DESCENDING)],
                background=True,
            )
            mongo_db[MONGODB_NAME]["tasks"].create_index(
                ["project_id", "test_id", "flag", ("created_at", pymongo.DESCENDING)],
                background=True,
            )
            mongo_db[MONGODB_NAME]["tasks"].create_index(
                ["project_id", "test_id", ("created_at", pymongo.ASCENDING)],
                background=True,
            )
            mongo_db[MONGODB_NAME]["tasks"].create_index(
                ["project_id", "flag"], background=True
            )
            mongo_db[MONGODB_NAME]["tasks"].create_index(
                "metadata.version_id", background=True
            )
            mongo_db[MONGODB_NAME]["tasks"].create_index(
                "metadata.user_id", background=True
            )
            mongo_db[MONGODB_NAME]["tasks"].create_index(
                "last_eval.source", background=True
            )

            # Evals
            mongo_db[MONGODB_NAME]["evals"].create_index(
                "id", unique=True, background=True
            )
            mongo_db[MONGODB_NAME]["evals"].create_index("task_id", background=True)
            mongo_db[MONGODB_NAME]["evals"].create_index("session_id", background=True)
            mongo_db[MONGODB_NAME]["evals"].create_index("test_id", background=True)
            mongo_db[MONGODB_NAME]["evals"].create_index(
                ["project_id", "source", "value"], background=True
            )

            # Events
            mongo_db[MONGODB_NAME]["events"].create_index(
                "id", unique=True, background=True
            )
            mongo_db[MONGODB_NAME]["events"].create_index(
                ["id", "task_id", "removed"], background=True
            )
            mongo_db[MONGODB_NAME]["events"].create_index(
                ["id", "session_id", "removed"], background=True
            )
            mongo_db[MONGODB_NAME]["events"].create_index(
                ["task_id", "removed"], background=True
            )
            mongo_db[MONGODB_NAME]["events"].create_index(
                ["session_id", "removed"], background=True
            )
            mongo_db[MONGODB_NAME]["events"].create_index("removed", background=True)
            mongo_db[MONGODB_NAME]["events"].create_index("event_name", background=True)
            mongo_db[MONGODB_NAME]["events"].create_index("project_id", background=True)
            mongo_db[MONGODB_NAME]["events"].create_index("session_id", background=True)
            mongo_db[MONGODB_NAME]["events"].create_index("task_id", background=True)
            mongo_db[MONGODB_NAME]["events"].create_index(
                [("created_at", pymongo.DESCENDING)], background=True
            )
            mongo_db[MONGODB_NAME]["events"].create_index(
                ["project_id", ("created_at", pymongo.DESCENDING)], background=True
            )

            try:
                # if the view exists, delete it
                if (
                    "sessions_with_events"
                    in await mongo_db[MONGODB_NAME].list_collection_names()
                ):
                    await mongo_db[MONGODB_NAME]["sessions_with_events"].drop()
                await mongo_db[MONGODB_NAME].command(
                    {
                        "create": "sessions_with_events",
                        "viewOn": "sessions",
                        "pipeline": [
                            {
                                "$lookup": {
                                    "from": "events",
                                    "localField": "id",
                                    "foreignField": "session_id",
                                    "as": "events",
                                },
                            },
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
                        ],
                    }
                )
            except Exception:
                logger.info("sessions_with_events already exists")
            try:
                if (
                    "tasks_with_events"
                    in await mongo_db[MONGODB_NAME].list_collection_names()
                ):
                    await mongo_db[MONGODB_NAME]["tasks_with_events"].drop()
                await mongo_db[MONGODB_NAME].command(
                    {
                        "create": "tasks_with_events",
                        "viewOn": "tasks",
                        "pipeline": [
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
                        ],
                    }
                )
            except Exception:
                logger.info("tasks_with_events already exists")

            # EventDefinitions
            mongo_db[MONGODB_NAME]["event_definitions"].create_index(
                "id", unique=True, background=True
            )
            mongo_db[MONGODB_NAME]["event_definitions"].create_index(
                ["project_id", "id"], background=True
            )
            mongo_db[MONGODB_NAME]["event_definitions"].create_index(
                "event_name", background=True
            )

            mongo_db[MONGODB_NAME]["private-clusters"].create_index(
                "id", unique=True, background=True
            )
            mongo_db[MONGODB_NAME]["private-clusters"].create_index(
                "project_id", background=True
            )
            mongo_db[MONGODB_NAME]["job_results"].create_index(
                ["project_id", "job_metadata.id"], background=True
            )
            mongo_db[MONGODB_NAME]["recipes"].create_index("id", background=True)

        except Exception as e:
            logger.warning(f"Error while connecting to Mongo: {e}")
            raise e
    except Exception as e:
        logger.exception(f"Could not connect to mongo: {e}")
        raise e


async def close_mongo_db():
    global mongo_db
    if mongo_db is None:
        logger.warning("Connection is None, nothing to close.")
        return
    mongo_db.close()
    mongo_db = None
    logger.info("Mongo connection closed.")

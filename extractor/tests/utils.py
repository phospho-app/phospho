import logging
from typing import Dict, List

import pymongo

logger = logging.getLogger(__name__)


def cleanup(
    mongo_db: pymongo.MongoClient,
    collections_to_cleanup: Dict[str, List[str]],
) -> None:
    """
    DELETE the documents in the collections specified in the collections_to_cleanup dict

    collections_to_cleanup is a dict of {collection_name: [list of ids]}
    those ids will be used to DELETE the documents in the collection
    """
    # Clean up database after the test
    if mongo_db.name != "production":
        for collection, values in collections_to_cleanup.items():
            logger.info(f"Cleaning up {len(values)} documents in {collection}")
            mongo_db[collection].delete_many({"id": {"$in": values}})
        logger.info("Database cleaned up after test")
    else:
        raise RuntimeError(
            "You are trying to clean the production database. Set MONGODB_NAME to something else than 'production'"
        )

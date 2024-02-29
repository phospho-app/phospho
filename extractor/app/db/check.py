"""
The python code to check that the documents in the NoSQL Database match de pydantic models
"""
from loguru import logger
from app.db.client import firestore_db as firestore_db  # The actual firestore client


def validate_collection(collection_name: str, model) -> bool:
    """
    Check that the documents in the collection match the pydantic model
    """
    docs = firestore_db.collection(collection_name).stream()

    for doc in docs:
        try:
            item = model(id=doc.id, **doc.to_dict())
        except Exception as e:
            logger.warning(
                f"Error with document {doc.id} in collection {collection_name}"
            )
            logger.warning(doc.to_dict())
            logger.warning(e)
            return False

    return True

from typing import Literal, Optional
from ai_hub.db.mongo import get_mongo_db
from ai_hub.core import config

from dataclasses import dataclass


@dataclass
class ProgressBar:
    project_id: str
    clustering_id: Optional[str] = None

    status: Optional[
        Literal[
            "started",
            "loading_existing_embeddings",
            "generating_new_embeddings",
            "generate_clusters",
            "generate_clusters_description_and_title",
            "merging_similar_clusters",
            "saving_clusters",
        ]
    ] = None
    number_embeddings: int = 0
    number_embeddings_processed: int = 0
    number_clusters: int = 0
    number_clusters_processed: int = 0
    percent_of_completion: float = 0.0
    percent_of_completion_in_db: float = 0.0
    # Minimum change in percent_of_completion to save to the database
    min_save_delta: float = 1

    async def update(
        self,
        new_embeddings_processed: Optional[int] = None,
    ) -> None:
        """
        Update the progress bar with the given status.
        """

        mongo_db = await get_mongo_db()

        percent_of_completion = self.percent_of_completion

        if self.status == "loading_existing_embeddings":
            if new_embeddings_processed is not None:
                self.number_embeddings_processed += new_embeddings_processed
            else:
                self.number_embeddings_processed += 1
            percent_of_completion = (
                self.number_embeddings_processed / self.number_embeddings
            ) * 70
        elif self.status == "generating_new_embeddings":
            self.number_embeddings_processed += 1
            percent_of_completion = (
                self.number_embeddings_processed / self.number_embeddings
            ) * 70

        elif self.status == "generate_clusters_description_and_title":
            self.number_clusters_processed += 1
            percent_of_completion = (
                70 + (self.number_clusters_processed / self.number_clusters) * 25
            )

        elif self.status == "saving_clusters":
            percent_of_completion = 100

        if (
            abs(percent_of_completion - self.percent_of_completion_in_db)
            > self.min_save_delta
        ):
            # Only update the db if significative increase
            await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
                {"id": self.clustering_id},
                {"$set": {"percent_of_completion": percent_of_completion}},
            )
            self.percent_of_completion_in_db = percent_of_completion

        # Update the percent of completion
        self.percent_of_completion = percent_of_completion

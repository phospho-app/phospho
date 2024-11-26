import asyncio
import string
from typing import Dict, List, Literal, Optional, Union

from ai_hub.models.progress_bar import ProgressBar
from ai_hub.models.users import User
from ai_hub.services.summaries import generate_cluster_description_title
import numpy as np
from loguru import logger
from openai import AsyncOpenAI
from sklearn.cluster import DBSCAN, AgglomerativeClustering  # type: ignore
from sklearn.decomposition import PCA  # type: ignore
from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
from sklearn.preprocessing import OneHotEncoder  # type: ignore


from ai_hub.core import config
from ai_hub.models.clusterings import Cluster
from ai_hub.models.embeddings import Embedding
from phospho.models import Session, Task

openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


def generate_clusters(
    embeddings: np.ndarray,
    eps: float = 0.05,
    min_samples: int = 5,
    n_components: int = -1,
    nb_clusters: Optional[int] = None,
    min_nb_clusters: int = 5,
    average_cluster_size: int = 100,
    clustering_mode: Literal["dbscan", "agglomerative"] = "agglomerative",
):
    """
    If clustering_mode is dbscan, run db scan.
    If clustering_mode is agglomerative and nb_clusters is not None and more than min_nb_clusters, then run it with nb_clusters.
    If clustering_mode is agglomerative and nb_clusters is None, then use the average_cluster_size to determine number of parameters.
    """

    logger.debug(f"Clustering mode: {clustering_mode}")

    if len(embeddings) == 0:
        logger.error("No embeddings to cluster")
        return []

    # Reduce the dimensionality of the embeddings using PCA
    if n_components < embeddings.shape[1] and n_components > 0:
        n_components = embeddings.shape[1]
    if n_components > 0:
        embeddings = PCA(n_components=n_components).fit_transform(embeddings)

    # TODO : More heuristics on the algo to use based on the number of embeddings?

    logger.debug(f"nb clusters: {nb_clusters}")

    if clustering_mode == "dbscan":
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(embeddings)
    elif clustering_mode == "agglomerative":
        if nb_clusters is None or nb_clusters == 0:
            nb_clusters = max(min_nb_clusters, len(embeddings) // average_cluster_size)
        if nb_clusters > len(embeddings):
            nb_clusters = len(embeddings)
        clustering = AgglomerativeClustering(
            n_clusters=nb_clusters,
        ).fit(embeddings)
    else:
        raise ValueError(f"Clustering mode {clustering_mode} not supported")

    return clustering.labels_


async def generate_clusters_description_title(
    clusters: List[Cluster],
    embeddings: Dict[str, Embedding],
    datas: Dict[str, Union[Task, Session, User]],
    progress_bar: ProgressBar,
    output_format: Literal[
        "title_description", "user_persona", "question_and_answer"
    ] = "title_description",
    openai_model_id: str = "gpt-4o",
    max_samples: int = 15,
    instruction: Optional[str] = "user intent",
) -> List[Cluster]:
    """
    Generate a description for a cluster.

    The description is based on a list of text messages.
    """

    # Generate a summary of the clusters using an LLM
    clusters = await asyncio.gather(
        *(
            generate_cluster_description_title(
                cluster=cluster,
                embeddings=embeddings,
                datas=datas,
                progress_bar=progress_bar,
                output_format=output_format,
                instruction=instruction,
                openai_model_id=openai_model_id,
                max_samples=max_samples,
            )
            for cluster in clusters
        )
    )

    return clusters


def merge_similar_clusters(clusters: List[Cluster]) -> List[Cluster]:
    """
    Merge similar clusters by comparing the descriptions.
    If the descripions share more than 80% of the words, merge them.

    The title and description of the merged cluster will be one of the cluster.
    """

    tokenized_names: List[List[str]] = []
    for cluster in clusters:
        if cluster.name is None:
            tokenized_names.append([])
        else:
            tokenized_names.append(
                [
                    word.strip(string.punctuation)
                    for word in cluster.name.lower().split()
                ]
            )

    all_words = [word for description in tokenized_names for word in description]

    encoder = OneHotEncoder(sparse_output=False)
    encoder.fit(np.array(all_words).reshape(-1, 1))

    names_one_hot = np.stack(
        [
            np.sum(encoder.transform(np.array(description).reshape(-1, 1)), axis=0)
            for description in tokenized_names
        ]
    )

    # If a word is present twice, I want it to be 1 anyway
    names_one_hot[names_one_hot > 0] = 1

    # Compute the similarity between the clusters
    # Because the clusters name does not have the same length, I normalize the similarity by using cosine similarity
    similarities = cosine_similarity(names_one_hot)
    np.fill_diagonal(similarities, 0)
    similarities = np.triu(similarities)

    clusters_to_keep = [True] * len(clusters)

    # I take the highest similarity and merge the clusters ; then I set the similarity to 0 on the column of the cluster_donnor
    # Maximum iterations is the number of clusters (linear complexity)
    while np.argmax(similarities) > 1:
        i, j = np.unravel_index(np.argmax(similarities), similarities.shape)

        cluster_receiver = clusters[i]
        cluster_donor = clusters[j]
        cluster_receiver.size += cluster_donor.size
        if cluster_receiver.description is None:
            cluster_receiver.description = cluster_donor.description

        if cluster_receiver.tasks_ids is None:
            cluster_receiver.tasks_ids = cluster_donor.tasks_ids
        else:
            cluster_receiver.tasks_ids.extend(cluster_donor.tasks_ids or [])
        if cluster_receiver.sessions_ids is None:
            cluster_receiver.sessions_ids = cluster_donor.sessions_ids
        else:
            cluster_receiver.sessions_ids.extend(cluster_donor.sessions_ids or [])
        if cluster_receiver.embeddings_ids is None:
            cluster_receiver.embeddings_ids = cluster_donor.embeddings_ids
        else:
            cluster_receiver.embeddings_ids.extend(cluster_donor.embeddings_ids or [])

        similarities[:, j] = 0
        clusters_to_keep[j] = False

    clusters = [cluster for i, cluster in enumerate(clusters) if clusters_to_keep[i]]

    return clusters

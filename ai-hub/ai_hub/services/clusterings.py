import os
from collections import defaultdict
import time
from typing import Dict, List, Literal, Optional, Union

from ai_hub.db.users import load_users
from ai_hub.models.progress_bar import ProgressBar
from ai_hub.models.users import User
from ai_hub.services.clusters import (
    generate_clusters,
    generate_clusters_description_title,
    merge_similar_clusters,
)
import numpy as np
import resend
from loguru import logger
from openai import AsyncOpenAI
from sklearn.decomposition import PCA  # type: ignore

from ai_hub.core import config
from ai_hub.db.mongo import get_mongo_db
from ai_hub.db.sessions import load_sessions
from ai_hub.db.tasks import load_tasks
from ai_hub.models.clusterings import Cluster, Clustering
from ai_hub.models.embeddings import Embedding
from ai_hub.services.embeddings import (
    generate_datas_embeddings,
    get_project_embeddings,
)
from phospho.models import ProjectDataFilters, Session, Task

openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


async def generate_project_clustering(
    project_id: str,
    org_id: Optional[str] = None,
    limit: Optional[int] = 4000,
    filters: Optional[ProjectDataFilters] = None,
    model: Literal[
        "intent-embed", "intent-embed-2", "intent-embed-3"
    ] = "intent-embed-3",
    batch_size: int = 1024,
    scope: Literal["messages", "sessions", "users"] = "messages",
    instruction: Optional[str] = "user intent",
    nb_clusters: Optional[int] = None,
    merge_clusters: bool = False,
    clustering_mode: Literal["agglomerative", "dbscan"] = "agglomerative",
    clustering_id: Optional[str] = None,
    clustering_name: Optional[str] = None,
    user_email: Optional[str] = None,
    output_format: Literal[
        "title_description", "user_persona", "question_and_answer"
    ] = "title_description",
) -> Optional[Clustering]:
    """
    Generate a clustering for a project
    """
    logger.info(f"Generating clustering for project: {project_id} ; limit: {limit}")
    clustering_start_time = time.time()
    mongo_db = await get_mongo_db()
    progress_bar = ProgressBar(
        project_id=project_id,
        clustering_id=clustering_id,
        status="started",
    )

    if filters is None:
        filters = ProjectDataFilters()

    # Createe the clustering object for status tracking
    clustering = Clustering(
        org_id=org_id,
        project_id=project_id,
        type="intent-unsupervised",
        nb_clusters=None,  # To be filled later
        clusters_ids=[],  # To be filled later
        status="started",  # To be updated later
        percent_of_completion=None,
        filters=filters,
        model=model,
        scope=scope,
        instruction=instruction,
        pca={},  # To be filled later
    )
    # Initialize the percent of completion
    # If the clustering_id and clustering_name are provided, use them
    if clustering_id is not None:
        clustering.id = clustering_id
    if clustering_name is not None:
        clustering.name = clustering_name
    await mongo_db[config.CLUSTERINGS_COLLECTION].insert_one(clustering.model_dump())

    datas: Union[List[Task], List[Session], List[User], None]
    if scope == "messages":
        # Load the tasks for the project
        datas = await load_tasks(
            project_id=project_id,
            filters=filters,
            clustering=clustering,
            limit=limit,
        )
    elif scope == "sessions":
        # Load the sessions for the project
        datas = await load_sessions(
            project_id=project_id,
            filters=filters,
            clustering=clustering,
            limit=limit,
        )
    elif scope == "users":
        datas = await load_users(
            project_id=project_id,
            clustering=clustering,
            filters=filters,
            limit=limit,
        )
    else:
        raise ValueError(
            f"messages_or_sessions should be 'messages', 'sessions' or 'users, got {scope}"
        )
    if datas is None:
        datas = []

    progress_bar.number_embeddings = len(datas)
    progress_bar.status = "loading_existing_embeddings"
    await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
        {"id": clustering.id},
        {"$set": {"status": "loading_existing_embeddings"}},
    )

    # Get the up to "limit" number of embeddings for the tasks of the project
    embeddings = await get_project_embeddings(
        project_id,
        progress_bar=progress_bar,
        batch_size=batch_size,
        datas=datas,
        model=model,
        instruction=instruction,
    )
    logger.debug(f"Nb Embeddings: {len(embeddings)}")

    # Get the list of data that don't have an embedding yet
    existing_embeddings: List[Union[Task, Session, User]] = []
    embeddings_to_clusterize: List[Embedding] = []
    task_id_to_embedding = {embedding.task_id: embedding for embedding in embeddings}
    session_id_to_embedding = {
        embedding.session_id: embedding for embedding in embeddings
    }
    user_id_to_embedding = {embedding.user_id: embedding for embedding in embeddings}

    for data in datas:
        if isinstance(data, Task):
            embedding = task_id_to_embedding.get(data.id)
        elif isinstance(data, Session):
            embedding = session_id_to_embedding.get(data.id)
        elif isinstance(data, User):
            embedding = user_id_to_embedding.get(data.id)

        if embedding is not None:
            embeddings_to_clusterize.append(embedding)
            existing_embeddings.append(data)

    logger.debug(f"existing embeddings: {len(existing_embeddings)}")

    # Filter the datas without embeddings. We will generate the embeddings for them
    datas_without_embeddings = [
        data for data in datas if data not in existing_embeddings
    ]
    logger.debug(f"nb Embeddings we have to compute: {len(datas_without_embeddings)}")

    progress_bar.number_embeddings_processed = len(existing_embeddings)
    progress_bar.status = "generating_new_embeddings"
    await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
        {"id": clustering.id},
        {"$set": {"status": "generating_new_embeddings"}},
    )

    if len(datas_without_embeddings) > 0:
        new_embeddings = await generate_datas_embeddings(
            datas_without_embeddings,
            len_datas=len(datas),
            emb_model=clustering.model,
            scope=scope,
            instruction=instruction,
            clustering=clustering,
            progress_bar=progress_bar,
        )
        # Save the embeddings to the database in one dump
        if len(new_embeddings) == 0:
            logger.warning("No new embeddings generated, skipping")
        else:
            mongo_db[config.EMBEDDINGS_COLLECTION].insert_many(
                [embedding.model_dump() for embedding in new_embeddings]
            )
            logger.debug("New embeddings saved")

            # Merge the new embeddings with the existing ones
            embeddings_to_clusterize.extend(new_embeddings)

    logger.debug(f"nb Embeddings for clustering: {len(embeddings_to_clusterize)}")
    if len(embeddings_to_clusterize) == 0:
        logger.error(
            f"Project: {project_id}, model: {model}, scope: {scope}, instruction: {instruction}"
            + "No embeddings found to clusterize. "
            + "This is due to an issue when calling the embeddings API."
        )

    # Comvert embedings list as np arrays
    clustering_embeddings_array = np.array(
        [embedding.embeddings for embedding in embeddings_to_clusterize]
    )
    logger.info(f"Embeddings array shape: {clustering_embeddings_array.shape}")
    if clustering_embeddings_array.shape[0] == 0:
        raise ValueError(
            "No embeddings found to clusterize. Verify you have properly setup the embeddings API"
        )

    progress_bar.status = "generate_clusters"
    await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
        {"id": clustering.id},
        {"$set": {"status": "generate_clusters"}},
    )
    # Generate clusters
    labels = generate_clusters(
        clustering_embeddings_array,
        nb_clusters=nb_clusters,
        clustering_mode=clustering_mode,
    )

    clusters_labels: Dict[int, List[int]] = defaultdict(list)
    for i, label in enumerate(labels):
        # i is the row index of the embedding in clustering_embeddings_array and embeddings_for_all_tasks
        clusters_labels[label].append(i)

    clusters: List[Cluster] = []
    for cluster_label, item_in_cluster_indexes in clusters_labels.items():
        embeddings_ids: List[str] = []
        tasks_ids: List[str] = []
        sessions_ids: List[str] = []
        users_ids: List[str] = []
        for i in item_in_cluster_indexes:
            embeddings_ids.append(embeddings_to_clusterize[i].id)
            task_id = embeddings_to_clusterize[i].task_id
            if task_id is not None:
                tasks_ids.append(task_id)
            session_id = embeddings_to_clusterize[i].session_id
            if session_id is not None:
                sessions_ids.append(session_id)
            user_id = embeddings_to_clusterize[i].user_id
            if user_id is not None:
                users_ids.append(user_id)
        cluster = Cluster(
            model=model,
            org_id=org_id,
            project_id=project_id,
            clustering_id=clustering.id,
            size=len(clusters_labels[cluster_label]),
            tasks_ids=tasks_ids,
            sessions_ids=sessions_ids,
            users_ids=users_ids,
            scope=scope,
            instruction=instruction,
            embeddings_ids=embeddings_ids,
        )
        clusters.append(cluster)

    logger.info(
        f"nb clusters: {len(clusters)} for {len(embeddings_to_clusterize)} embeddings in this clustering"
    )
    # Update the clustering object with the number of clusters
    clustering.status = "summaries"
    await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
        {"id": clustering.id},
        {"$set": {"status": "summaries"}},
    )

    progress_bar.status = "generate_clusters_description_and_title"
    await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
        {"id": clustering.id},
        {"$set": {"status": "generate_clusters_description_and_title"}},
    )
    progress_bar.number_clusters = len(clusters)

    embeddings_ids_to_embeddings = {
        embedding.id: embedding for embedding in embeddings_to_clusterize
    }

    datas_ids_to_datas = {data.id: data for data in datas}

    clusters = await generate_clusters_description_title(
        clusters=clusters,
        embeddings=embeddings_ids_to_embeddings,
        datas=datas_ids_to_datas,
        progress_bar=progress_bar,
        output_format=output_format,
        instruction=instruction,
    )

    logger.info(f"Generated {len(clusters)} clusters")
    if merge_clusters:
        progress_bar.status = "merging_similar_clusters"
        await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
            {"id": clustering.id},
            {"$set": {"status": "merging_similar_clusters"}},
        )
        logger.info("Merging similar clusters")
        clusters = merge_similar_clusters(clusters)

    progress_bar.status = "saving_clusters"
    await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
        {"id": clustering.id},
        {"$set": {"status": "saving_clusters"}},
    )

    clustering.nb_clusters = len(clusters)
    await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
        {"id": clustering.id},
        {"$set": {"nb_clusters": clustering.nb_clusters}},
    )

    await progress_bar.update()

    # Save the clusters in the database
    mongo_db[config.CLUSTERS_COLLECTION].insert_many(
        [cluster.model_dump() for cluster in clusters]
    )

    embedding_id_to_cluster_id = {}
    embedding_id_to_cluster_name = {}
    for cluster in clusters:
        for embedding_id in cluster.embeddings_ids or []:
            embedding_id_to_cluster_id[embedding_id] = cluster.id
            embedding_id_to_cluster_name[embedding_id] = cluster.name

    pca = PCA(n_components=3)
    dim_reduction_results: np.ndarray = pca.fit_transform(clustering_embeddings_array)

    pca = {
        "x": [res[0] for i, res in enumerate(dim_reduction_results)],
        "y": [res[1] for i, res in enumerate(dim_reduction_results)],
        "z": [res[2] for i, res in enumerate(dim_reduction_results)],
        "clusters_ids": [
            embedding_id_to_cluster_id[embedding.id]
            for embedding in embeddings_to_clusterize
        ],
        "embeddings_ids": [embedding.id for embedding in embeddings_to_clusterize],
    }

    # Update the clustering object with the clusters ids
    clustering.clusters_ids = [cluster.id for cluster in clusters]
    clustering.status = "completed"
    await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
        {"id": clustering.id},
        {
            "$set": {
                "clusters_ids": clustering.clusters_ids,
                "status": "completed",
                "percent_of_completion": 100,
                "pca": pca,
            }
        },
    )

    logger.info(f"Clustering {clustering.id} saved for project {project_id}")

    # Use Resend to send a notification mail if > 60s of computation
    if time.time() - clustering_start_time > 60 and user_email is not None:
        logger.info(
            f"Sending email notification for {clustering.name} to email {user_email}"
        )
        try:
            resend.api_key = config.RESEND_API_KEY
            params = resend.Emails.SendParams(
                **{
                    "from": "phospho <contact@phospho.ai>",
                    "to": [user_email],
                    "subject": f"Clustering {clustering.name} completed",
                    "html": f"""<p>Hello!<br><br>This is a notification email to tell you that your clustering '{clustering.name}' has finished running.</p>
                <p><br>Go to the phospho platform to check out the results.</p>
                <p>Cheers,<br>
                The Phospho Team</p>
                """,
                }
            )
            resend.Emails.send(params)
        except Exception as e:
            logger.error(
                f"Clustering email notification failed project {clustering.project_id} to email {user_email}:\n{e}"
            )
    else:
        logger.info(
            f"Skipping email notification for {clustering.name} to email {user_email} after {time.time() - clustering_start_time} seconds"
        )

    return clustering

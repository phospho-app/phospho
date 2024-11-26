from typing import Dict, List, Optional

from phospho_backend.api.platform.models.explore import ClusteringEmbeddingCloud
from phospho_backend.db.mongo import get_mongo_db
from fastapi import HTTPException
from loguru import logger

from phospho.models import Cluster, Clustering


async def rename_clustering(project_id: str, clustering_id: str, new_name: str):
    """
    Rename a clustering.
    """
    mongo_db = await get_mongo_db()

    result = await mongo_db["private-clusterings"].update_one(
        {"id": clustering_id, "project_id": project_id},
        {"$set": {"name": new_name}},
    )

    logger.debug(f"Renamed clustering {clustering_id} to {new_name}")
    logger.debug(f"{result}")


async def get_date_last_clustering_timestamp(
    project_id: str,
) -> Optional[int]:
    """
    Get the timestamp date of the last clustering for a given project.
    """
    mongo_db = await get_mongo_db()

    result = (
        await mongo_db["private-clusterings"]
        .find({"project_id": project_id})
        .sort([("created_at", -1)])
        .limit(1)
        .to_list(length=1)
    )
    if len(result) == 0:
        return None
    date_last_clustering_timestamp = result[0]["created_at"]
    return date_last_clustering_timestamp


async def get_last_clustering_composition(
    project_id: str,
) -> Optional[List[Dict[str, object]]]:
    """
    Get the composition of the last clustering for a given project.
    """
    mongo_db = await get_mongo_db()

    clustering = (
        await mongo_db["private-clusterings"]
        .find({"project_id": project_id, "status": "completed"})
        .sort([("created_at", -1)])
        .limit(1)
        .to_list(length=1)
    )
    if len(clustering) == 0:
        return None

    clusters = (
        await mongo_db["private-clusters"]
        .find(
            {"clustering_id": clustering[0]["id"]},
            {"name": 1, "description": 1, "size": 1},
        )
        .to_list(length=None)
    )
    clusters = [
        {"name": c["name"], "description": c["description"], "size": c["size"]}
        for c in clusters
    ]
    return clusters


async def fetch_all_clusterings(
    project_id: str,
    limit: int = 100,
    with_cluster_names: bool = True,
) -> List[Clustering]:
    """
    Fetch all the clusterings of a project. The clusterings are sorted by creation date.

    Each clustering contains clusters.
    """
    mongo_db = await get_mongo_db()

    pipeline: List[Dict[str, object]] = [
        {"$match": {"project_id": project_id}},
    ]
    if with_cluster_names:
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "private-clusters",
                        "localField": "id",
                        "foreignField": "clustering_id",
                        "as": "clusters",
                    }
                },
                {"$project": {"pca": 0, "tsne": 0}},
            ]
        )

    pipeline += [
        {"$sort": {"created_at": -1}},
    ]
    clusterings = (
        await mongo_db["private-clusterings"].aggregate(pipeline).to_list(length=limit)
    )
    if not clusterings:
        return []
    valid_clusterings = [
        Clustering.model_validate(clustering) for clustering in clusterings
    ]
    return valid_clusterings


async def fetch_all_clusters(
    project_id: str, clustering_id: Optional[str] = None, limit: int = 100
) -> List[Cluster]:
    """
    Fetch the clusters of a project.

    If the clustering (group of clusters) is not specified, the latest clustering is used.
    """
    mongo_db = await get_mongo_db()
    # Get the latest clustering
    if clustering_id is None:
        get_latest_clustering = (
            await mongo_db["private-clusterings"]
            .find({"project_id": project_id})
            .sort([("created_at", -1)])
            .to_list(length=1)
        )
        if len(get_latest_clustering) == 0:
            return []
        latest_clustering = get_latest_clustering[0]
        clustering_id = latest_clustering.get("id")

    # Retrieve the clusters of the clustering
    clusters = (
        await mongo_db["private-clusters"]
        .find(
            {
                "project_id": project_id,
                "clustering_id": clustering_id,
            }
        )
        .to_list(length=limit)
    )
    valid_clusters = [Cluster.model_validate(cluster) for cluster in clusters]
    return valid_clusters


async def fetch_single_cluster(project_id: str, cluster_id: str) -> Optional[Cluster]:
    """
    Fetch a single cluster from a project
    """
    mongo_db = await get_mongo_db()
    cluster = await mongo_db["private-clusters"].find_one(
        {"project_id": project_id, "id": cluster_id}
    )
    if cluster is None:
        return None
    valid_cluster = Cluster.model_validate(cluster)
    return valid_cluster


async def compute_cloud_of_clusters(
    project_id: str,
    version: ClusteringEmbeddingCloud,
) -> dict:
    """
    Get the embeddings for the clustering project.
    Compute a PCA on the embeddings and return the first three components if the version is PCA.
    Compute a TSNE on the embeddings and return the first three components if the version is TSNE.
    """
    if version.type != "pca":
        raise NotImplementedError(f"Type {version.type} is not implemented")

    mongo_db = await get_mongo_db()
    collection_name = "private-clusterings"
    pipeline: List[Dict[str, object]] = [
        {
            "$match": {
                "project_id": project_id,
                "id": version.clustering_id,
                version.type: {"$exists": True},
            }
        },
    ]

    raw_results = await mongo_db[collection_name].aggregate(pipeline).to_list(length=1)
    if raw_results is None or raw_results == []:
        return {}

    clustering_model = Clustering.model_validate(raw_results[0])

    # Check if the clustering model has the required field
    if version.type == "pca":
        cloud_of_points = clustering_model.pca
    if version.type == "tsne":
        cloud_of_points = clustering_model.tsne
    # TODO: If new type of embedding is added, add the corresponding code here

    # If the clustering isn't finished, cloud_of_points is None. Return early
    if cloud_of_points is None or cloud_of_points == {}:
        return {}

    if "clusters_names" in cloud_of_points.keys():
        # Old data model
        dim_reduction_results = cloud_of_points
    else:
        # New model.
        # TODO : Version the models in cloud_of_point
        # Get the task_id or the session_id from the embeddings_ids in raw_results[0]["pca"]
        collection_name = "private-embeddings"
        embeddings_ids = cloud_of_points["embeddings_ids"]
        pipeline = [
            {
                "$match": {
                    "project_id": project_id,
                    "id": {"$in": embeddings_ids},
                }
            },
            {"$project": {"task_id": 1, "session_id": 1, "user_id": 1}},
        ]

        scope_ids = (
            await mongo_db[collection_name].aggregate(pipeline).to_list(length=None)
        )
        if clustering_model.scope == "messages":
            scope_ids = [scope_id["task_id"] for scope_id in scope_ids]
        elif clustering_model.scope == "sessions":
            scope_ids = [scope_id["session_id"] for scope_id in scope_ids]
        elif clustering_model.scope == "users":
            scope_ids = [scope_id["user_id"] for scope_id in scope_ids]

        # Get the clusters names from the clusters_ids in raw_results[0]["pca"]
        # I want a cluster name for each cluster_id
        collection_name = "private-clusters"
        pipeline = [
            {
                "$match": {
                    "project_id": project_id,
                    "id": {"$in": cloud_of_points["clusters_ids"]},
                }
            },
            {"$project": {"name": 1, "id": 1}},
        ]

        clusters_ids_to_clusters_names = (
            await mongo_db[collection_name].aggregate(pipeline).to_list(length=None)
        )
        clusters_ids_to_clusters_names = {
            cluster_id_to_cluster_name["id"]: cluster_id_to_cluster_name["name"]
            for cluster_id_to_cluster_name in clusters_ids_to_clusters_names
        }

        clusters_names = [
            clusters_ids_to_clusters_names[cluster_id]
            for cluster_id in cloud_of_points["clusters_ids"]
        ]
        dim_reduction_results = cloud_of_points
        del dim_reduction_results["embeddings_ids"]
        dim_reduction_results["ids"] = scope_ids
        dim_reduction_results["clusters_names"] = clusters_names

    return dim_reduction_results


async def get_clustering_by_id(
    project_id: str,
    clustering_id: str,
    fetch_clouds: bool = False,
) -> Clustering:
    """
    Get a clustering based on its id.

    If fetch_clouds is False, the pca and tsne fields are not returned. This is useful when the embeddings are not needed.
    """
    mongo_db = await get_mongo_db()
    collection_name = "private-clusterings"
    pipeline: List[Dict[str, object]] = [
        {
            "$match": {
                "project_id": project_id,
                "id": clustering_id,
            }
        },
    ]
    if not fetch_clouds:
        pipeline.append({"$project": {"_id": 0, "pca": 0, "tsne": 0}})

    raw_results = await mongo_db[collection_name].aggregate(pipeline).to_list(length=1)
    if raw_results is None or raw_results == []:
        raise HTTPException(
            status_code=404,
            detail=f"Clustering {clustering_id} not found in project {project_id}",
        )

    clustering_model = Clustering.model_validate(raw_results[0])
    return clustering_model

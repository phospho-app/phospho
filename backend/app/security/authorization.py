from app.db.mongo import get_mongo_db
from app.security.authentification import propelauth
from app.services.mongo.organizations import get_usage_quota


async def get_quota(project_id: str) -> dict:
    """
    Get the quota of a project
    """
    mongo_db = await get_mongo_db()
    project = await mongo_db["projects"].find_one({"id": project_id})
    if not project:
        raise ValueError(f"Project {project_id} not found for quota")
    org_id = project["org_id"]
    org = propelauth.fetch_org(org_id)
    if not org:
        raise ValueError(f"Organization {org_id} not found for quota")
    org_plan = "hobby"
    org_metadata = org.get("metadata", None)
    if org_metadata:
        org_plan = org_metadata.get("plan", "hobby")
    usage = await get_usage_quota(org_id, org_plan)
    return usage


async def authorize_main_pipeline(project_id: str) -> bool:
    """
    Authorize the main pipeline of a project
    """
    mongo_db = await get_mongo_db()

    # Get the org_id from the project document in the db
    project = await mongo_db["projects"].find_one({"id": project_id})
    if not project:
        raise ValueError(f"Project {project_id} not found for authorization")
    # Get the organization plan from the propelauth metadata
    org_id = project["org_id"]
    org = propelauth.fetch_org(org_id)
    if not org:
        raise ValueError(f"Organization {org_id} not found for authorization")

    # Default org_plan: org_plan = "hobby"
    org_plan = "hobby"

    # Get the org plan
    org_metadata = org.get("metadata", None)

    if org_metadata:
        org_plan = org_metadata.get("plan", "hobby")

    # Get the usage quota
    usage = await get_usage_quota(org_id, org_plan)

    if usage["max_usage"] is None:
        return True
    else:
        return usage["credits"] > 0

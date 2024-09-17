import httpx
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger


from app.core import config
from app.security import authenticate_org_key
from app.api.v2.models.tak_search import SearchRequest, SearchResponse

router = APIRouter(tags=["tak-search"])


@router.post("/search", response_model=SearchResponse)
async def post_search(
    request: SearchRequest,
    org: dict = Depends(authenticate_org_key),
):
    """
    Retrieve chunks from a website for a given search query


    """
    org_metadata = org["org"].get("metadata", {})

    # Check that the org has access to the completion service
    if not org_metadata.get("has_tak_search_access", False):
        raise HTTPException(
            status_code=402,
            detail="You need to request access to this feature to the phospho team. Please contact us at contact@phospho.ai",
        )

    # TODO: add a check on the Stripe customer ID

    # Use HTTPX to call the tak search service
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{config.TAK_SEARCH_URL}/v1/search",  # Replace with the actual URL
            json={
                "query": request.query,
                "domain": request.domain,
                "max_results": request.max_results,
                "include_raw_content": request.include_raw_content,
            },
            headers={"Authorization": f"Bearer {config.TAK_APP_API_KEY}"},
        )

        response_json = response.json()

        if response.status_code != 200:
            logger.error(response_json)
            raise HTTPException(
                status_code=response.status_code,
                detail="An error occurred while fetching the search results",
            )

        try:
            # Load as a SearchResponse object
            response_object = SearchResponse(**response_json)
            return response_object

        except Exception as e:
            logger.error(f"Error loading the response: {e}")
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing the search results",
            )

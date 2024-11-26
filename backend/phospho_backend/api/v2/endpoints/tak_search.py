import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.requests import Request
from fastapi_simple_rate_limiter import rate_limiter  # type: ignore
from loguru import logger


from phospho_backend.core import config
from phospho_backend.security import authenticate_org_key
from phospho_backend.api.v2.models.tak_search import SearchRequest, SearchResponse

router = APIRouter(tags=["tak-search"])


@router.post("/search", response_model=SearchResponse)
@rate_limiter(limit=50, seconds=60)
async def post_search(
    search_request: SearchRequest,
    request: Request,
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

    # Log the request
    logger.info(
        f"Search request from {org['org']['org_id']} for search_request: {search_request}"
    )

    # Use HTTPX to call the tak search service
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{config.TAK_SEARCH_URL}/v1/search",  # Replace with the actual URL
            json={
                "query": search_request.query,
                "domain": search_request.domain,
                "max_results": search_request.max_results,
                "include_raw_content": search_request.include_raw_content,
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

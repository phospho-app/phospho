from pydantic import BaseModel
from typing import Optional, List


class SearchRequest(BaseModel):
    query: str
    domain: str  # The domain for the search
    max_results: Optional[int] = 5
    include_raw_content: Optional[bool] = (
        False  # Include the cleaned and parsed HTML content of each search result.
    )


class SearchResults(BaseModel):
    title: str
    url: str
    content: str
    raw_content: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResults]

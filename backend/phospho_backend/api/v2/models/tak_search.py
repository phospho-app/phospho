from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    domain: str  # The domain for the search
    max_results: int | None = 5
    include_raw_content: bool | None = (
        False  # Include the cleaned and parsed HTML content of each search result.
    )


class SearchResults(BaseModel):
    title: str
    url: str
    content: str
    raw_content: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchResults]

from fastapi import APIRouter, Query, Response
from api.endpoints.property_search.controller import PropertySearchController
from api.endpoints.property_search.models import PropertySearchResponse

router = APIRouter()
controller = PropertySearchController()

@router.get("/properties/search", response_model=PropertySearchResponse)
def search_properties(
    response: Response,
    q: str | None = Query(None, description="Full text search"),
    county: str | None = Query(None, description="County filter"),
    status: str | None = Query(None, description="Property status"),
    min_price: float | None = Query(None, description="Minimum price"),
    max_price: float | None = Query(None, description="Maximum price"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=1000, description="Results per page"),
    sort: str | None = Query(None, description="Sort field"),
    direction: str | None = Query(None, description="Sort direction"),
):
    params = {
        "q": q,
        "county": county,
        "status": status,
        "min_price": min_price,
        "max_price": max_price,
        "page": page,
        "limit": limit,
        "sort": sort,
        "direction": direction,
    }
    result = controller.handle(params)
    # set X-Total-Count header if present
    if "total" in result:
        response.headers["X-Total-Count"] = str(result["total"])
    return result

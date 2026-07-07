from fastapi import APIRouter
from api.models.search_index import SearchIndex

router = APIRouter()
index = SearchIndex()

@router.get("/")
def search(q: str):
    results = index.search(q)
    return {"count": len(results), "results": results}

    results = []

    for r in data:
        if (
            q in (r.get("parcel_id") or "").upper()
            or q in (r.get("address") or "").upper()
            or q in (r.get("owner") or "").upper()
            or (r.get("landbank") and q in (r["landbank"].get("program", "").upper()))
            or (r.get("landbank") and q in (r["landbank"].get("status", "").upper()))
        ):
            results.append(r)

    return {"count": len(results), "results": results}

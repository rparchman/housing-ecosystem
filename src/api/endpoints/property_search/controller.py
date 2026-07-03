from typing import Dict, Any
from .validation import PropertySearchValidator
from .service import PropertySearchService

class PropertySearchController:
    def __init__(self):
        self.validator = PropertySearchValidator()
        self.service = PropertySearchService()

    def handle(self, request_params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            filters = self.validator.validate(request_params)
        except ValueError as e:
            return {"status": 400, "errors": e.args[0]["errors"]}

        # Build a readable query for logs (optional)
        query_str = self.service.build_query(filters)
        print(f"[PropertySearchController] query: {query_str}")

        # Call the service with filters directly (no SQL parsing)
        result = self.service.execute_query(filters)
        rows = result.get("rows", [])
        total = result.get("total", 0)

        limit = filters.get("limit", 25)
        page = filters.get("page", 1)
        total_pages = (total + limit - 1) // limit if limit > 0 else 1

        return {
            "status": 200,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "results": rows,
        }

from typing import Any, Dict

class PropertySearchValidator:
    VALID_SORT_FIELDS = {"price", "sqft", "created_at"}
    VALID_DIRECTIONS = {"asc", "desc"}
    VALID_STATUS = {"available", "pending", "sold"}

    def validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        try:
            page = int(params.get("page", 1))
        except Exception:
            errors.append("page must be an integer")
            page = 1
        try:
            limit = int(params.get("limit", 25))
        except Exception:
            errors.append("limit must be an integer")
            limit = 25

        if page < 1:
            errors.append("page must be >= 1")
        if limit < 1 or limit > 1000:
            errors.append("limit must be between 1 and 1000")

        sort = params.get("sort")
        direction = params.get("direction")
        status = params.get("status")

        if sort and sort not in self.VALID_SORT_FIELDS:
            errors.append(f"invalid sort field: {sort}")
        if direction and direction not in self.VALID_DIRECTIONS:
            errors.append(f"invalid direction: {direction}")
        if status and status not in self.VALID_STATUS:
            errors.append(f"invalid status: {status}")

        if errors:
            raise ValueError({"errors": errors})

        return {
            "page": page,
            "limit": limit,
            "status": status,
            "sort": sort,
            "direction": direction,
            "min_price": params.get("min_price"),
            "max_price": params.get("max_price"),
            "county": params.get("county"),
            "q": params.get("q"),
        }


from typing import Dict, Any, List

class PropertySearchService:
    def build_query(self, filters: Dict[str, Any]) -> str:
        conditions = []
        if filters.get("q"):
            q = filters["q"].replace("'", "''")
            conditions.append(f"(address ILIKE '%{q}%' OR city ILIKE '%{q}%' OR parcel_id ILIKE '%{q}%')")
        if filters.get("county"):
            county = str(filters["county"]).replace("'", "''")
            conditions.append(f"county = '{county}'")
        if filters.get("status"):
            status = str(filters["status"]).replace("'", "''")
            conditions.append(f"status = '{status}'")

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        sort_field = filters.get("sort", "created_at")
        direction = filters.get("direction", "desc")
        limit = filters.get("limit", 25)
        offset = (filters.get("page", 1) - 1) * limit

        query = (
            f"SELECT * FROM properties WHERE {where_clause} "
            f"ORDER BY {sort_field} {direction} LIMIT {limit} OFFSET {offset};"
        )
        return query

    def execute_query(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[PropertySearchService] execute_query called with filters: {filters}")
        all_rows = [
            {"id": "prop-001", "address": "123 Main St", "city": "Flat Rock", "county": "Wayne", "price": 250000, "sqft": 1400, "status": "available"},
            {"id": "prop-002", "address": "456 Oak Ave", "city": "Flat Rock", "county": "Wayne", "price": 320000, "sqft": 1800, "status": "available"},
            {"id": "prop-003", "address": "789 Pine Rd", "city": "Flat Rock", "county": "Wayne", "price": 185000, "sqft": 1100, "status": "pending"},
            {"id": "prop-004", "address": "101 Maple Ln", "city": "Flat Rock", "county": "Wayne", "price": 410000, "sqft": 2200, "status": "available"},
            {"id": "prop-005", "address": "202 Birch Blvd", "city": "Flat Rock", "county": "Wayne", "price": 275000, "sqft": 1500, "status": "sold"},
            {"id": "prop-006", "address": "Test House 1", "city": "Testville", "county": "Wayne", "price": 100000, "sqft": 900, "status": "available"},
            {"id": "prop-007", "address": "Test Cottage", "city": "Flat Rock", "county": "Wayne", "price": 150000, "sqft": 1100, "status": "available"},
        ]

        q = filters.get("q")
        if q:
            q_lower = q.lower()
            filtered = [
                r for r in all_rows
                if q_lower in r["address"].lower()
                or q_lower in r["city"].lower()
                or q_lower in r.get("parcel_id", "").lower()
            ]
        else:
            filtered = all_rows

        total = len(filtered)
        page = max(int(filters.get("page", 1)), 1)
        limit = max(int(filters.get("limit", 25)), 1)
        start = (page - 1) * limit
        end = start + limit
        page_rows = filtered[start:end]

        return {"rows": page_rows, "total": total}

from typing import List, Optional
from pydantic import BaseModel

class PropertyModel(BaseModel):
    id: str
    address: str
    city: str
    county: Optional[str] = None
    price: Optional[int] = None
    sqft: Optional[int] = None
    status: Optional[str] = None

class PropertySearchResponse(BaseModel):
    status: int
    page: int
    limit: int
    total: int
    total_pages: int
    results: List[PropertyModel]

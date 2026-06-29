from pydantic import BaseModel
from typing import Optional, Dict

class Listing(BaseModel):
    listing_id: str
    address: str
    meta: Dict
    va_tag: bool = False

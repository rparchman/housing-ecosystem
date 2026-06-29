from pydantic import BaseModel

class Listing(BaseModel):
    listing_id: str
    address: str
    meta: dict
    va_tag: bool = False

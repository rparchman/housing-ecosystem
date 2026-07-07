from fastapi import FastAPI

from api.routes.contractor.router import router as contractor_router
from api.routes.listings.router import router as listings_router
from api.routes.property_search.router import router as property_search_router

app = FastAPI()

# include routers (order does not matter)
app.include_router(contractor_router)
app.include_router(listings_router)
app.include_router(property_search_router)


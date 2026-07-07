from fastapi import FastAPI
from api.routes import parcels, landbank, search, analytics

app = FastAPI(
    title="Michigan Housing Ecosystem API",
    version="1.0.0",
    description="Statewide parcel + land bank intelligence API"
)

# Register routes
app.include_router(parcels.router, prefix="/parcels", tags=["Parcels"])
app.include_router(landbank.router, prefix="/landbank", tags=["Land Bank"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

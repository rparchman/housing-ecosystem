from fastapi import APIRouter
from services.contractor.job_controller import router as contractor_router

router = APIRouter()
router.include_router(contractor_router)

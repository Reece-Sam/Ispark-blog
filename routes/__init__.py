from fastapi import APIRouter

from routes.blogs import router as blogs_router


router = APIRouter()

router.include_router(blogs_router)
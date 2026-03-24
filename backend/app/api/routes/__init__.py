from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.eval import router as eval_router
from app.api.routes.health import router as health_router
from app.api.routes.traces import router as traces_router

router = APIRouter()
router.include_router(health_router)
router.include_router(chat_router)
router.include_router(traces_router)
router.include_router(eval_router)

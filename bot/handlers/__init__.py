from aiogram import Router

from .start import router as start_router
from .subscribe import router as subscribe_router
from .profile import router as profile_router


def setup_routers() -> Router:
    """Setup all routers."""
    router = Router()
    router.include_router(start_router)
    router.include_router(subscribe_router)
    router.include_router(profile_router)
    return router

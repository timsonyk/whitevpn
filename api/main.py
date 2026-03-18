import asyncio
import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from core.config import settings
from core.database import db
from api.routes.config import router as config_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    await db.connect()
    logging.info("Database connected")
    yield
    # Shutdown
    await db.close()


# Create FastAPI app
app = FastAPI(
    title="WhiteLis VPN API",
    description="API for serving VPN configs to subscribers",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(config_router)


def main():
    """Run the API server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()

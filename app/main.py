import asyncio
import logging
from fastapi import FastAPI
from app.api.endpoints import resources, health, consumers
from app.core.config import load_config
from app.grpc_service.server import serve

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("app")

load_config("app/config/")

# app = FastAPI(title="Game Resource Distributor")
#
# # Include routers
# app.include_router(resources.router, prefix="/resources", tags=["resources"])
# app.include_router(consumers.router, prefix="/consumers", tags=["consumers"])
# app.include_router(health.router, tags=["health"])


try:
    asyncio.run(serve())
except KeyboardInterrupt:
    print("Shutting down server.")

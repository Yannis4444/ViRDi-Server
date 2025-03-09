import logging
from fastapi import FastAPI
from app.api.endpoints import resources, health

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("app")

app = FastAPI(title="Game Resource Distributor")

# Include routers
app.include_router(resources.router, prefix="/resources", tags=["resources"])
app.include_router(health.router, tags=["health"])

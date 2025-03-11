import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas.consumers import ConsumerCreated
from app.services.prosumer import Consumer, Resource

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create", response_model=ConsumerCreated)
async def produce(consumer_id: str, resource_id: str):
    consumer = Consumer.get(consumer_id)

    if consumer is not None:
        logger.warning(f"Consumer '{consumer_id}' already exists and will not be recreated")
        raise HTTPException(status_code=409, detail="Consumer already exists")

    resource = Resource.get(resource_id)

    if resource is None:
        logger.error(f"Resource '{resource_id}' not found")
        raise HTTPException(status_code=404, detail="Resource not found")

    # TODO: buffer limit should come from some config
    consumer = await Consumer.create(consumer_id, resource, 100)

    return ConsumerCreated(
        id=consumer_id,
    )

import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas.resource import ProducedResource, ConsumedResource
from app.services.consumer import get_consumer
from app.services.producer import get_producer
from app.services.resource import get_resource

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/produce", response_model=ProducedResource)
async def produce(producer_id: str, resource_id: str, amount: int):
    producer = await get_producer(producer_id)

    if producer is None:
        logger.error(f"Producer '{producer_id}' not found")
        raise HTTPException(status_code=404, detail="Producer not found")

    resource = await get_resource(resource_id)

    if resource is None:
        logger.error(f"Resource '{resource_id}' not found")
        raise HTTPException(status_code=404, detail="Resource not found")

    produced_amount = await producer.produce(resource, amount)

    return ProducedResource(
        amount=produced_amount,
    )


@router.post("/consume", response_model=ConsumedResource)
async def consume(consumer_id: str, resource_id: str, amount: int):
    consumer = await get_consumer(consumer_id)

    if consumer is None:
        logger.error(f"Consumer '{consumer_id}' not found")
        raise HTTPException(status_code=404, detail="Consumer not found")

    resource = await get_resource(resource_id)

    if resource is None:
        logger.error(f"Resource '{resource_id}' not found")
        raise HTTPException(status_code=404, detail="Resource not found")

    consumed_amount = await consumer.consume(resource, amount)

    return ProducedResource(
        amount=consumed_amount,
    )
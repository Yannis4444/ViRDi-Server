import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas.resource import ProducedResource, ConsumedResource
from app.services.prosumer import get_consumer, get_producer

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/produce", response_model=ProducedResource)
async def produce(producer_id: str, resource_id: str, amount: int):
    producer = await get_producer(producer_id, resource_id=resource_id)

    if producer is None:
        logger.error(f"Producer '{producer_id}' not found")
        raise HTTPException(status_code=404, detail="Producer not found")

    produced_amount = await producer.produce(amount)

    return ProducedResource(
        amount=produced_amount,
    )


@router.post("/consume", response_model=ConsumedResource)
async def consume(consumer_id: str, resource_id: str, amount: int):
    consumer = await get_consumer(consumer_id, resource_id)

    if consumer is None:
        logger.error(f"Consumer '{consumer_id}' not found")
        raise HTTPException(status_code=404, detail="Consumer not found")

    consumed_amount = await consumer.consume(amount)

    return ProducedResource(
        amount=consumed_amount,
    )
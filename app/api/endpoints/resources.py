import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas.resources import ResourceProduced, ResourceConsumed, ProduceResource
from app.services.prosumer import Consumer, Resource

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/produce", response_model=ResourceProduced)
async def produce(resource_id: str, amount: int):
    resource = Resource.get(resource_id)

    if resource is None:
        logger.error(f"Resource '{resource_id}' not found")
        raise HTTPException(status_code=404, detail="Resource not found")

    produced_amount = await resource.add(amount)

    return ResourceProduced(
        amount=produced_amount,
    )


@router.post("/produce", response_model=ResourceProduced)
async def produce(produce: ProduceResource):
    resource = Resource.get(produce.resource_id)

    if resource is None:
        logger.error(f"Resource '{produce.resource_id}' not found")
        raise HTTPException(status_code=404, detail="Resource not found")

    produced_amount = await resource.add(produce.amount)

    return ResourceProduced(
        amount=produced_amount,
    )


@router.post("/consume", response_model=ResourceConsumed)
async def consume(consumer_id: str, amount: int):
    # TODO: only allow for consumers without notifier
    consumer = Consumer.get(consumer_id)

    if consumer is None:
        logger.error(f"Consumer '{consumer_id}' not found")
        raise HTTPException(status_code=404, detail="Consumer not found")

    if consumer.notifier is not None:
        logger.error(f"Consumer '{consumer_id}' with defined notifier cannot be consumed manually")
        raise HTTPException(status_code=404, detail="Consumers with defined notifier cannot be consumed manually")

    consumed_amount = await consumer.remove(amount)

    return ResourceProduced(
        amount=consumed_amount,
    )
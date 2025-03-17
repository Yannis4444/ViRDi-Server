import logging

from fastapi import APIRouter, HTTPException

from virdi.api.schemas.consumers import ConsumerCreated
from virdi.services.notify import get_notifier_class
from virdi.services.prosumer import Consumer, Resource

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create", response_model=ConsumerCreated)
async def produce(consumer_id: str, resource_id: str, notifier_type: str | None = None, notifier_config: dict | None = None):
    consumer = Consumer.get(consumer_id)

    if consumer is not None:
        logger.warning(f"Consumer '{consumer_id}' already exists and will not be recreated")
        raise HTTPException(status_code=409, detail="Consumer already exists")

    resource = Resource.get(resource_id)

    if resource is None:
        logger.error(f"Resource '{resource_id}' not found")
        raise HTTPException(status_code=404, detail="Resource not found")

    notifier = None
    if notifier_type is not None:
        notifier_class = get_notifier_class(notifier_type)

        if notifier_class is None:
            logger.error(f"Notifier type '{notifier_type}' does not exist")
            raise HTTPException(status_code=404, detail="Notifier type does not exist")

        notifier = notifier_class(notifier_config)

    # TODO: buffer limit should come from some config
    consumer = await Consumer.create(consumer_id, resource, 100, notifier=notifier)

    return ConsumerCreated(
        id=consumer_id,
    )

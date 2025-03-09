import asyncio
import logging

from app.services.resource import get_resource, Resource

logger = logging.getLogger(__name__)


class Consumer:
    """
    An abstract base class that defines the interface for a Consumer.
    """

    def __init__(self, consumer_id: str):
        """
        Creates a new consumer

        :param consumer_id: An identifier for the consumer
        """

        self._consumer_id = consumer_id

    def __repr__(self):
        return f"Consumer(consumer_id={self._consumer_id})"

    def __str__(self):
        return self._consumer_id

    async def consume(self, resource: Resource | str, amount: int) -> int:
        """
        Adds an amount of the resource and returns how much was actually stored.

        When the storage limit is reached, the return value will be less than the set amount.

        :param resource: The type of resource to be consumed, represented as a string.
        :param amount: The quantity of the resource to be consumed, represented as an integer.
        :return: The amount that was actually stored.
        """

        if isinstance(resource, str):
            resource = await get_resource(resource)

        actual_amount = await resource.consume(amount)

        logger.info(f"{self} consumed ({actual_amount}/{amount}) of {resource}")

        return actual_amount


_consumer_creation_lock = asyncio.Lock()
_consumers: dict[str, Consumer] = {}


async def get_consumer(consumer_id) -> Consumer:
    """
    Gets the consumer with the given id.
    Should always be used to get any consumer

    :param consumer_id: The identifier for the consumer to get
    :return: The consumer
    """

    # TODO: later not just create one but use the config?

    if consumer_id not in _consumers:
        async with _consumer_creation_lock:
            if consumer_id not in _consumers:
                _consumers[consumer_id] = Consumer(consumer_id)

    return _consumers.get(consumer_id)

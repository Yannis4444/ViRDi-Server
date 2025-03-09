import asyncio
import logging

from app.services.resource import get_resource, Resource

logger = logging.getLogger(__name__)


class Producer:
    """
    An abstract base class that defines the interface for a Producer.
    """

    def __init__(self, producer_id: str):
        """
        Creates a new producer

        :param producer_id: An identifier for the producer
        """

        self._producer_id = producer_id

    def __repr__(self):
        return f"Producer(producer_id={self._producer_id})"

    def __str__(self):
        return self._producer_id

    async def produce(self, resource: Resource | str, amount: int) -> int:
        """
        Adds an amount of the resource and returns how much was actually stored.

        When the storage limit is reached, the return value will be less than the set amount.

        :param resource: The type of resource to be produced, represented as a string.
        :param amount: The quantity of the resource to be produced, represented as an integer.
        :return: The amount that was actually stored.
        """

        if isinstance(resource, str):
            resource = await get_resource(resource)

        actual_amount = await resource.produce(amount)

        logger.info(f"{self} produced ({actual_amount}/{amount}) of {resource}")

        return actual_amount


_producer_creation_lock = asyncio.Lock()
_producers: dict[str, Producer] = {}


async def get_producer(producer_id) -> Producer:
    """
    Gets the producer with the given id.
    Should always be used to get any producer

    :param producer_id: The identifier for the producer to get
    :return: The producer
    """

    # TODO: later not just create one but use the config?

    if producer_id not in _producers:
        async with _producer_creation_lock:
            if producer_id not in _producers:
                _producers[producer_id] = Producer(producer_id)

    return _producers.get(producer_id)

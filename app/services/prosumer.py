import asyncio
import logging

logger = logging.getLogger(__name__)


class Resource:
    """
    Representation of a resource.
    Only one instance should exist for each type of resource
    """

    def __init__(self, resource_id: str, buffer_limit: int, buffer: int = 0):
        """
        Creates a new resource.

        :param resource_id: A resource identifier
        :param buffer_limit: The maximum amount of the resource that can be stored at once
        :param buffer: The starting buffer of the resource
        """

        self._id = resource_id
        self._buffer_limit = buffer_limit

        self._buffer = buffer
        self._buffer_lock = asyncio.Lock()

        self._consumers: set[Consumer] = set()

    def __repr__(self) -> str:
        return f"Resource(resource_id={self._id}, buffer_limit={self._buffer_limit}, buffer={self._buffer})"

    def __str__(self) -> str:
        return self._id

    @property
    def id(self) -> str:
        """
        The identifier for the resource

        :return: The id
        """

        return self._id

    def add_consumer(self, consumer: 'Consumer'):
        """
        Adds the given consumer to be considered when producing

        :param consumer: The consumer to add
        """

        # TODO: option to remove

        self._consumers.add(consumer)

    async def produce(self, amount: int) -> int:
        """
        Adds an amount of the resource and returns how much was actually stored.

        When the storage buffer limit is reached, the return value will be less than the set amount.

        :param amount: The amount of the resource to be produced.
        :return: The amount that was actually stored.
        """

        # first put the produced amount into the buffers of the consumers
        consumers = list(self._consumers)
        while amount > 0 and consumers:
            amount_per_consumer = amount // len(_consumers)
            n_consumers_additional_resource = amount % len(_consumers)
            next_consumers = []

            for i, consumer in enumerate(consumers):
                # TODO: rotate distribution of remainder - not just always the first ones
                consumer_amount = amount_per_consumer + (1 if i < n_consumers_additional_resource else 0)
                actual_amount = await consumer.add_to_buffer(consumer_amount)

                if actual_amount == consumer_amount:
                    # The consumer might still take more of the resource if anything remains
                    next_consumers.append(consumer)

                amount -= actual_amount

            consumers = next_consumers

        if amount > 0:
            async with self._buffer_lock:
                actual_amount = min(amount, self._buffer_limit - self._buffer)
                self._buffer += actual_amount

        logging.info(repr(self))
        logging.info(self._consumers)

        return actual_amount

    async def consume(self, amount: int) -> int:
        """
        Removes an amount of the resource and returns how much was actually taken.

        When the storage is empty, the return value will be less than the set amount.

        :param amount: The amount of the resource to be consumed.
        :return: The amount that was actually consumed.
        """

        async with self._buffer_lock:
            actual_amount = min(amount, self._buffer)
            self._buffer -= actual_amount
            return actual_amount


_resource_creation_lock = asyncio.Lock()
_resources: dict[str, Resource] = {}


async def get_resource(resource_id) -> Resource:
    """
    Gets the resource with the given id.
    Should always be used to get any resource

    :param resource_id: The identifier for the resource to get
    :return: The resource
    """
    if resource_id not in _resources:
        async with _resource_creation_lock:
            if resource_id not in _resources:
                # TODO: actual buffer limit
                _resources[resource_id] = Resource(resource_id, 100)

    return _resources.get(resource_id)


class Prosumer:
    """
    Abstract base class for both Producer and Consumer.
    """

    def __init__(self, prosumer_id: str, resource: Resource):
        """
        Creates a new consumer

        :param prosumer_id: An identifier for the consumer
        :param resource: The resource this consumer consumes.
        """

        self._id = prosumer_id
        self._resource = resource

    def __repr__(self):
        return f"Prosumer(id={self._id}, resource={self._resource})"

    def __str__(self):
        return self._id

    @property
    def resource(self) -> Resource:
        """
        The resource the prosumer is handling

        :return: The resource
        """

        return self._resource


class Producer(Prosumer):
    """
    Defines the interface for a Producer.
    """

    def __init__(self, producer_id: str, resource: Resource):
        """
        Creates a new producer

        :param producer_id: An identifier for the producer
        :param resource: The resource this consumer consumes.
        """

        super().__init__(producer_id, resource)

    def __repr__(self):
        return f"Producer(id={self._id}, resource={self._resource})"

    async def produce(self, amount: int) -> int:
        """
        Adds an amount of the handled resource and returns how much was actually stored.

        When the storage limit is reached, the return value will be less than the set amount.

        :param amount: The quantity of the resource to be produced, represented as an integer.
        :return: The amount that was actually stored.
        """

        actual_amount = await self.resource.produce(amount)

        logger.info(f"{self} produced {actual_amount}/{amount} of {self.resource}")

        return actual_amount


class Consumer(Prosumer):
    """
    Defines the interface for a Consumer.
    """

    def __init__(self, consumer_id: str, resource: Resource, buffer_limit: int, buffer: int = 0):
        """
        Creates a new consumer

        :param consumer_id: An identifier for the consumer
        :param resource: The resource this consumer consumes.
        :param buffer_limit: The maximum amount of the resource that can be stored at once
        :param buffer: The starting buffer of the resource
        """

        super().__init__(consumer_id, resource)

        resource.add_consumer(self)

        self._buffer_limit = buffer_limit
        self._buffer = buffer
        self._buffer_lock = asyncio.Lock()

    def __repr__(self):
        return f"Consumer(id={self._id}, resource={self._resource}, buffer_limit={self._buffer_limit}, buffer={self._buffer})"

    def __str__(self):
        return self._id

    async def add_to_buffer(self, amount: int) -> int:
        """
        Adds the given amount to the local consumer buffer

        When the storage limit is reached, the return value will be less than the set amount.

        :param amount: The amount to add
        :return: The amount actually added
        """

        async with self._buffer_lock:
            actual_amount = min(amount, self._buffer_limit - self._buffer)
            self._buffer += actual_amount
            return actual_amount

    async def consume(self, amount: int) -> int:
        """
        Adds an amount of the handled resource and returns how much was actually stored.

        When the buffer is emptied, the return value will be less than the set amount.

        :param amount: The quantity of the resource to be consumed, represented as an integer.
        :return: The amount that was actually stored.
        """

        # first try to take from the global resource buffer
        actual_amount = await self._resource.consume(amount)

        # take rest from consumer buffer
        if actual_amount < amount:
            async with self._buffer_lock:
                additional_amount = min(amount - actual_amount, self._buffer)
                actual_amount += additional_amount
                self._buffer -= additional_amount

        logger.info(f"{self} consumed {actual_amount}/{amount} of {self.resource}")

        return actual_amount


_consumer_creation_lock = asyncio.Lock()
_consumers: dict[str, Consumer] = {}


async def get_consumer(consumer_id: str, resource_id: str) -> Consumer:
    """
    Gets the consumer with the given id.
    Should always be used to get any consumer

    :param consumer_id: The identifier for the consumer to get
    :param resource_id: The identifier for the handled resource
    :return: The consumer
    """

    if consumer_id not in _consumers:
        async with _consumer_creation_lock:
            if consumer_id not in _consumers:
                # TODO: actual buffer settings
                _consumers[consumer_id] = Consumer(consumer_id, await get_resource(resource_id), 100)

    return _consumers.get(consumer_id)


_producer_creation_lock = asyncio.Lock()
_producers: dict[str, Producer] = {}


async def get_producer(producer_id: str, resource_id: str) -> Producer:
    """
    Gets the producer with the given id.
    Should always be used to get any producer

    :param producer_id: The identifier for the producer to get
    :param resource_id: The identifier for the handled resource
    :return: The producer
    """

    if producer_id not in _producers:
        async with _producer_creation_lock:
            if producer_id not in _producers:
                _producers[producer_id] = Producer(producer_id, await get_resource(resource_id))

    return _producers.get(producer_id)

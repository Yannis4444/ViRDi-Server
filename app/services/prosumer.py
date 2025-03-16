import asyncio
import logging
import random

from app.services.buffer import Buffer
from app.services.notify import Notifier

logger = logging.getLogger(__name__)


class Resource:
    """
    Representation of a resource.
    Only one instance should exist for each type of resource
    """

    _resources: dict[str, 'Resource'] = {}

    @classmethod
    def get(cls, resource_id) -> 'Resource | None':
        """
        Gets the resource with the given id.
        Should always be used to get any resource

        :param resource_id: The identifier for the resource to get
        :return: The resource or None if none exist yet
        """

        return cls._resources.get(resource_id)

    @classmethod
    def create_from_config(cls, config: dict) -> 'Resource':
        """
        Creates the resource from a config.

        Will not check that the resource does not exist yet!

        :param config: The config from the yaml files
        :return: The new resource
        :raises: ValueError if a value is wrong or missing
        """

        resource_id = config.get("id")
        buffer_limit = config.get("buffer_limit")

        if resource_id is None:
            raise ValueError(f"Found resource without id: {config}")

        if buffer_limit is None:
            raise ValueError(f"Found resource without buffer_limit: {config}")

        logger.info(f"Creating Resource '{resource_id}'")

        resource = cls(resource_id, buffer_limit)
        cls._resources[resource_id] = resource
        return resource

    def __init__(self, resource_id: str, buffer_limit: int, initial_buffer_amount: int = 0):
        """
        Creates a new resource.

        Should not be called directly.
        Use Resource.create() instead.

        :param resource_id: A resource identifier
        :param buffer_limit: The maximum amount of the resource that can be stored at once
        :param initial_buffer_amount: The buffer amount to start with
        """

        self._id = resource_id

        self._buffer = Buffer(buffer_limit, initial_buffer_amount)

        self._consumers: set[Consumer] = set()
        self._consumer_lock = asyncio.Lock()

        self._request_events: set[asyncio.Event] = set()

    def __repr__(self) -> str:
        return f"Resource(resource_id={self._id}, buffer={self._buffer})"

    def __str__(self) -> str:
        return self._id

    @property
    def id(self) -> str:
        """
        The identifier for the resource

        :return: The id
        """

        return self._id

    @property
    def buffer(self) -> Buffer:
        """
        The internally used buffer

        :return: The buffer
        """

        return self._buffer

    async def add_consumer(self, consumer: 'Consumer'):
        """
        Adds the given consumer to be considered when producing.

        Also fills the consumers buffer if anything is available in the resource buffer.

        :param consumer: The consumer to add
        """

        # TODO: option to remove

        async with self._consumer_lock:
            self._consumers.add(consumer)

        # give it whatever is in the global resource buffer
        if self._buffer.amount > 0:
            async with self._buffer.lock:
                await consumer.add(self._buffer.amount)
                await self._buffer.remove(consumer.buffer.amount, lock=False)
            await consumer.notify()

    async def add(self, amount) -> bool:
        """
        First tries to distribute the given amount to the buffers off registered consumers.
        Adds the remaining amount to the internal buffer.
        If the buffer is completely filled, the return value will be less than the set amount.

        If the buffer is already locked manually, lock can be set to False.

        :param amount: The amount to add
        :return: True as long as ViRDi still needs the resource
        """

        # TODO: rework distribute for new return logic
        keep_coming, affected_consumers = await Consumer.distribute(amount, list(self._consumers), self._buffer)

        for consumer in affected_consumers:
            await consumer.notify()

        return keep_coming

    async def remove(self, amount, lock=True) -> int:
        """
        Removes the given amount from the internal buffer.
        If the buffer is completely empty, the return value will be less than the set amount.

        If the buffer is already locked manually, lock can be set to False.

        :param amount: The amount to remove
        :param lock: If the amount should be locked during the operation
        :return: The amount actually removed
        """

        full_before = self._buffer.is_full()

        actual_amount = await self._buffer.remove(amount, lock)

        if full_before and not self._buffer.is_full():
            for event in self._request_events:
                event.set()

        return actual_amount

    def add_request_event(self, event: asyncio.Event):
        """
        Adds an event the resource can use to signal that the resources is needed.
        Whenever the buffer changes from full to no longer full, all are set to signal to the producers.
        If the buffer is not full when the event is added, it is set directly.
        """

        self._request_events.add(event)

        if not self._buffer.is_full():
            event.set()

    def remove_request_event(self, event: asyncio.Event):
        """
        Removes a previously added event for requesting resources.
        """

        self._request_events.discard(event)


class Consumer:
    """
    Defines the interface for a Consumer.
    """

    _consumers: dict[str, 'Consumer'] = {}
    _consumer_creation_lock = asyncio.Lock()

    @staticmethod
    async def distribute(amount: int, consumers: list['Consumer'], remainder_buffer: Buffer | None = None) -> tuple[bool, set['Consumer']]:
        """
        Distributes the given amount to the given consumers.
        Any remainder will be put into the remainder buffer.

        consumers will be shuffled to achieve fair distributions over multiple runs.

        :param amount: The amount to distribute
        :param consumers: The consumers to distribute to first
        :param remainder_buffer: The buffer to put into if anything is remaining
        :return: A bool signaling if the buffers can receive more and the affected consumers (not including remainder buffer)
        """

        # shuffle consumers
        distributable: list[Consumer] = consumers[:]
        random.shuffle(distributable)

        affected_consumers: set[Consumer] = set()

        remaining = amount

        # lock all consumers
        await asyncio.gather(*(consumer._buffer.lock.acquire() for consumer in consumers))

        try:
            while remaining > 0 and distributable:
                amount_per_consumer = remaining // len(distributable)
                n_consumers_additional_resource = remaining % len(distributable)
                next_distributable = []

                for i, consumer in enumerate(distributable):
                    amount_to_add = amount_per_consumer + (1 if i < n_consumers_additional_resource else 0)

                    actual_amount = min(consumer.buffer.limit - consumer.buffer.amount, amount_to_add)
                    await consumer.buffer.add(actual_amount, lock=False)

                    if actual_amount > 0:
                        affected_consumers.add(consumer)

                    if actual_amount == amount_to_add:
                        next_distributable.append(consumer)

                    remaining -= actual_amount

                distributable = next_distributable
        finally:
            # release all consumers
            for consumer in consumers:
                consumer._buffer.lock.release()

        if remaining and remainder_buffer is not None:
            # there is stuff remaining for the global buffer
            return await remainder_buffer.add(remaining), affected_consumers
        else:
            # not even touching the global buffer - more can be taken
            return True, affected_consumers

    @classmethod
    def get(cls, consumer_id) -> 'Consumer | None':
        """
        Gets the consumer with the given id.
        Should always be used to get any consumer

        :param consumer_id: The identifier for the consumer to get
        :return: The consumer or None if none exist yet
        """

        return cls._consumers.get(consumer_id)

    @classmethod
    async def create(cls, consumer_id, resource: Resource, buffer_limit: int = 100, initial_buffer_amount: int = 0, max_rate: int | None = None, notifier: Notifier | None = None) -> 'Consumer':
        """
        Creates the consumer with the given id and adds it to the resource.
        Should always be used to create any consumer.

        Will not check that the consumer does not exist yet!

        :param consumer_id: An identifier for the consumer
        :param resource: The resource this consumer consumes.
        :param buffer_limit: The maximum amount of the resource that can be stored at once.
        :param initial_buffer_amount: The buffer amount to start with.
        :param max_rate: The maximum rate the consumer can consume at (1/min).
        :param notifier: A notifier to be used when new resources become available.
        :return: The new consumer
        """

        # TODO: use max rate

        logger.info(f"Creating Consumer '{consumer_id}' for '{resource}' with {notifier if notifier else 'no notifier'}")

        async with cls._consumer_creation_lock:
            consumer = cls(consumer_id, resource, buffer_limit, initial_buffer_amount=initial_buffer_amount, notifier=notifier)
            await resource.add_consumer(consumer)
            cls._consumers[consumer_id] = consumer
            return consumer

    def __init__(self, consumer_id: str, resource: Resource, buffer_limit: int, initial_buffer_amount: int = 0, notifier: Notifier | None = None):
        """
        Creates a new consumer

        Should never be called directly.
        Use Consumer.create() instead.

        :param consumer_id: An identifier for the consumer
        :param resource: The resource this consumer consumes.
        :param buffer_limit: The maximum amount of the resource that can be stored at once.
        :param initial_buffer_amount: The buffer amount to start with.
        :param notifier: A notifier to be used when new resources become available.
        """

        self._id = consumer_id
        self._resource = resource

        self._buffer = Buffer(buffer_limit, initial_buffer_amount)

        self._notifier = notifier

    def __repr__(self):
        return f"Consumer(id={self._id}, resource={self._resource}, buffer={self._buffer})"

    def __str__(self):
        return self._id

    @property
    def id(self) -> str:
        """
        The identifier of the consumer

        :return: The id
        """

        return self._id

    @property
    def resource(self) -> Resource:
        """
        The resource the consumer is handling

        :return: The resource
        """

        return self._resource

    @property
    def buffer(self) -> Buffer:
        """
        The buffer the consumer is using

        :return: The buffer
        """

        return self._buffer

    @property
    def notifier(self) -> Notifier | None:
        """
        The internally used notifier

        :return: The notifier or None if none is set.
        """

        return self._notifier

    async def add(self, amount, lock=True) -> int:
        """
        Adds the given amount to the internal buffer.
        If the buffer is completely filled, the return value will be less than the set amount.

        If the buffer is already locked manually, lock can be set to False.

        :param amount: The amount to add
        :param lock: If the amount should be locked during the operation
        :return: The amount actually added
        """

        return await self._buffer.add(amount, lock)

    async def remove(self, amount, lock=True) -> int:
        """
        First tries to remove the given amount from the resource buffer.
        Removes the remaining amount from the internal buffer.
        If the buffer is completely empty, the return value will be less than the set amount.

        If the buffer is already locked manually, lock can be set to False.

        :param amount: The amount to remove
        :param lock: If the amount should be locked during the operation
        :return: The amount actually removed
        """

        amount -= await self.resource.remove(amount, lock)

        return await self._buffer.remove(amount, lock)

    async def remove_all(self, lock=True) -> int:
        """
        Works like remove but tries gets everything from the local and global buffer.

        If the buffer is already locked manually, lock can be set to False.

        :param lock: If the amount should be locked during the operation
        :return: The amount actually removed
        """

        amount = await self.resource.buffer.remove_all(lock)
        amount += await self._buffer.remove_all(lock)

        return amount

    async def notify(self):
        """
        Notifies the actual client for the consumer of any changes made to the buffer.

        Only this method will be albe to remove from the buffer if a notifier is set
        as the manual polling is disabled then.
        Therefore, any amount currently in the buffer can be promised to the consumer
        without needing to take it from the buffer directly.
        It can then later be removed from the buffer as long as the notifier is locked
        ensuring only one notify runs simultaneously.

        If no notifier is set for the consumer, nothing happens.
        In this case, the consumer can be manually consumed using the REST API

        If notify is a coroutine, a new task will be created.
        """

        async def f():
            async with self._notifier:
                if self._buffer.amount > 0:
                    if asyncio.iscoroutinefunction(self._notifier.notify):
                        taken_amount = await self._notifier.notify(self._buffer.amount, self._id)
                    else:
                        taken_amount = self._notifier.notify(self._buffer.amount, self._id)
                    if taken_amount is not None:
                        actual_amount = await self.remove(taken_amount)
                        if actual_amount < taken_amount:
                            logger.warning(f"Notifier for {self} removed more than was available on the buffer: {actual_amount} < {taken_amount}")

        if self._notifier is not None:
            if asyncio.iscoroutinefunction(self._notifier.notify):
                asyncio.create_task(f())
            else:
                await f()

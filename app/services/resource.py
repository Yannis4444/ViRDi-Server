import asyncio
import logging

logger = logging.getLogger(__name__)


class Resource:
    """
    Representation of a resource.
    """

    def __init__(self, resource_id: str, limit: int, balance: int = 0):
        """
        Creates a new resource.

        :param resource_id: A resource identifier
        :param limit: The maximum amount of the resource that can be stored at once
        :param balance: The starting balance of the resource
        """

        self._resource_id = resource_id
        self._limit = limit

        self._balance = balance
        self._balance_lock = asyncio.Lock()

    def __repr__(self) -> str:
        return f"Resource(resource_id={self._resource_id}, limit={self._limit}, balance={self._balance})"

    def __str__(self) -> str:
        return self._resource_id

    @property
    def resource_id(self) -> str:
        """
        The identifier for the resource

        :return: The id
        """

        return self._resource_id

    async def produce(self, amount: int) -> int:
        """
        Adds an amount of the resource and returns how much was actually stored.

        When the storage limit is reached, the return value will be less than the set amount.

        :param amount: The amount of the resource to be produced.
        :return: The amount that was actually stored.
        """

        async with self._balance_lock:
            actual_amount = min(amount, self._limit - self._balance)
            self._balance += actual_amount
            return actual_amount

    async def consume(self, amount: int) -> int:
        """
        Removes an amount of the resource and returns how much was actually taken.

        When the storage is empty, the return value will be less than the set amount.

        :param amount: The amount of the resource to be consumed.
        :return: The amount that was actually consumed.
        """

        async with self._balance_lock:
            actual_amount = min(amount, self._balance)
            self._balance -= actual_amount
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
                # TODO: actual limit
                _resources[resource_id] = Resource(resource_id, 100)

    return _resources.get(resource_id)

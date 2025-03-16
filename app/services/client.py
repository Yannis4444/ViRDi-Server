import asyncio
import logging

import grpc
import uuid

from app.services.prosumer import Consumer, Resource

logger = logging.getLogger(__name__)


class Client:
    """
    An instance of a game server/instance
    """

    _clients: dict[str, 'Client'] = {}
    _client_creation_lock = asyncio.Lock()

    @classmethod
    async def get(cls, client_id: str) -> 'Client':
        """
        Get the client with the given id.
        If the client does not exist yet, one will be created.

        Should always be used to get a client

        :param client_id: The client id
        :return: The client
        """

        async with cls._client_creation_lock:
            if client_id not in cls._clients:
                cls._clients[client_id] = Client(client_id)
            return cls._clients[client_id]

    def __init__(self, client_id: str):
        """
        Create a new client.

        Do not use directly, use Client.get() instead.

        :param client_id: An identifier for the client
        """

        logger.info(f"New client {client_id}")

        self._id = client_id

        self._consumers: dict[str, Consumer] = {}

    def __repr__(self):
        return f"Client(id={self._id})"

    def __str__(self):
        return self._id

    @property
    def id(self):
        """
        The identifier for the client (not constant over reconnects)

        :return: The id
        """

        return self._id

    async def handle_resource_production(
            self,
            resource: Resource,
            amount: int
    ) -> bool:
        """
        Handles production of the given resource

        :param resource: The resource being produced
        :param amount: The amount produced
        :returns: True as long as ViRDi still needs the resource
        """

        return await resource.add(amount)

    async def handle_consumer_add(
            self,
            consumer_id: str,
            resource_id: str
    ):
        """
        Adds a consumer for this client

        :param consumer_id: The id for the consumer to add
        :param resource_id: The id for the resource the consumer consumes
        """

        logger.info(f"Adding consumer {consumer_id} for resource {resource_id} to client {self}")

        resource = Resource.get(resource_id)

        if resource is None:
            logger.error(f"Resource {resource_id} not found for new consumer {consumer_id} in client {self}")
            raise ValueError(f"Resource {resource_id} not found for new consumer {consumer_id}")

        consumer = Consumer.get(consumer_id)
        if consumer is not None:
            logger.warning(f"New consumer {consumer_id} for client {self} already exists")
        else:
            # TODO: notifier
            consumer = await Consumer.create(consumer_id, resource)

        self._consumers[consumer_id] = consumer

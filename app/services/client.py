import logging

import grpc
import uuid
from typing import AsyncIterator, Dict

from app.generated import virdi_pb2, virdi_pb2_grpc
from app.services.prosumer import Consumer, Resource

logger = logging.getLogger(__name__)


class Client:
    """
    An instance of a game server/instance
    """

    def __init__(self, grpc_context: grpc.aio.ServicerContext):
        """
        Create a new client

        :param grpc_context: The gRPC context of the client
        """

        self._id = str(uuid.uuid4())
        self._grpc_context = grpc_context

        logger.info(f"Creating client {self._id}")

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
            resource_id: str,
            amount: int
    ) -> bool:
        """
        Handles production of the given resource

        :param resource_id: The id of the resource
        :param amount: The amount produced
        :returns: True as long as ViRDi still needs the resource
        """

        resource = Resource.get(resource_id)

        if resource is None:
            logger.error(f"Resource {resource_id} not found for client {self}")
            raise ValueError(f"Resource {resource_id} not found")

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

import asyncio
import logging
from typing import AsyncIterator

import grpc

import app.grpc_service.proto.virdi_pb2 as pb2
import app.grpc_service.proto.virdi_pb2_grpc as pb2_grpc
from app.grpc_service.proto import virdi_pb2
from app.services.client import Client
from app.services.prosumer import Resource, Consumer

logger = logging.getLogger(__name__)


async def get_client_from_context(context: grpc.ServicerContext) -> Client | None:
    """
    Gets the client object from a given grpc context

    :param context: The servicer context
    :return: The client object
    """

    client_id = dict(context.invocation_metadata()).get("client-id")

    if client_id is None:
        return None

    return await Client.get(client_id)


class MyServiceServicer(pb2_grpc.VirdiServicer):
    async def OfferProduction(self, request: pb2.ProductionOffer, context: grpc.ServicerContext) -> AsyncIterator[pb2.ProductionRequest]:
        """
        A client offers the production of a resource, the server answers whenever the resource is needed
        """

        client = await get_client_from_context(context)
        if client is None:
            logging.error("Received production offer with missing or unknown client id")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Client not found or not given")

        resource = Resource.get(request.resource_id)
        if resource is None:
            logging.error(f"Received production offer from client {client} for unknown resource {request.resource_id}")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Unknown resource")

        logger.info(f"Client {client} started offering {resource}")

        request_event = asyncio.Event()
        resource.add_request_event(request_event)

        try:
            while True:
                await request_event.wait()

                logger.info(f"Sending production request for {resource} to {client}")
                yield pb2.ProductionRequest()

                request_event.clear()
        finally:
            resource.remove_request_event(request_event)
            logger.info(f"Client {client} stopped offering {resource}")

    async def Produce(self, request_iterator: AsyncIterator[pb2.ResourceProduction], context: grpc.ServicerContext) -> pb2.ProductionResponse:
        """
        A client sends resources in a stream.

        First message is expected to contain ResourceProductionInitInfo.

        The context is aborted with RESOURCE_EXHAUSTED once the buffer is full.
        """

        client = await get_client_from_context(context)
        if client is None:
            logging.error("Received production with missing or unknown client id")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Client not found or not given")

        first_message = await anext(request_iterator)
        resource_id = first_message.init_info.resource_id
        resource = Resource.get(resource_id)
        if resource is None:
            logging.error(f"Received production from client {client} with unknown resource {resource_id}")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Unknown resource")

        logger.info(f"Client {client} started sending {resource}")

        async for request in request_iterator:
            amount = request.amount

            if not await client.handle_resource_production(resource, amount):
                # buffer filled
                logger.info(f"Stopping client {client} from sending more {resource}")
                await context.abort(grpc.StatusCode.RESOURCE_EXHAUSTED, f"Buffer full, stop sending")
                break
        else:
            # Client stopped for sending resource on its own accord
            logger.info(f"Client {client} stopped sending {resource}")

        return virdi_pb2.ProductionResponse()

    async def Consume(self, request: pb2.ConsumptionRequest, context: grpc.ServicerContext) -> AsyncIterator[pb2.ResourceConsumption]:
        """
        A client requests resources, the server sends them in a stream.
        """

        client = await get_client_from_context(context)
        if client is None:
            logging.error("Received consumption request with missing or unknown client id")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Client not found or not given")

        max_rate = request.max_rate

        resource = Resource.get(request.resource_id)
        if resource is None:
            logging.error(f"Received production from client {client} with unknown resource {request.resource_id}")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Unknown resource")

        event = asyncio.Event()
        try:
            consumer = await client.add_consumer(request.consumer_id, resource, max_rate, event)
        except ValueError as e:
            logging.error(f"Failed to add consumer for consumption request for {resource} from {client}: {e}")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Failed to add consumer: {e}")

        logger.info(f"Starting sending {resource} to client {client} for consumer {consumer}")

        # maybe there is already something available - set event initially
        event.set()

        try:
            while True:
                await event.wait()

                # TODO: use max_rate here?
                # TODO: how much to take?
                amount = await consumer.remove_all()

                if amount > 0:
                    yield virdi_pb2.ResourceProduction(amount=amount)

                event.clear()
        finally:
            logger.info(f"Stopping sending {resource} to client {client} for consumer {consumer}")
            await client.remove_consumer(consumer.id)

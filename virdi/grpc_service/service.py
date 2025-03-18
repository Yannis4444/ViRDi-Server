import asyncio
import logging
import time
from typing import AsyncIterator

import grpc

import virdi.grpc_service.proto.virdi_pb2 as pb2
import virdi.grpc_service.proto.virdi_pb2_grpc as pb2_grpc
from virdi.grpc_service.proto import virdi_pb2
from virdi.metrics.metrics import production_metric
from virdi.services.client import Client
from virdi.services.prosumer import Resource, Consumer

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


def calculate_time_until_buffer_at_25(
        state_time: float,
        buffer_amount: float,
        buffer_limit: int,
        rate: int
) -> float:
    """
    Calculates the time until the buffer falls to 25% filling level.

    :param state_time: The time that the last_buffer_amount was calculated at
    :param buffer_amount: The amount in the buffer at the last time
    :param buffer_limit: The limit of the buffer
    :param rate: The rate the buffer is filled at (1/min)
    :return: The time until the buffer falls to 25% filling level in seconds or 0 if the buffer is already below 25%
    """

    buffer_25 = 0.25 * buffer_limit
    total_time_until_25 = (buffer_amount - buffer_25) / rate * 60
    time_until_25 = (state_time + total_time_until_25) - time.time()
    return max(time_until_25, 0.0)


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
            continue_production = await client.handle_resource_production(resource, amount)

            await production_metric(
                client.id,
                resource_id,
                amount
            )

            if not continue_production:
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

        By default, the server sends resources once every 10 seconds.
        If the buffer gets emptied, the server waits for new resources to restart sending.

        The Server aims to always fill the buffer to about 75% when it falls below 25%.

        The local buffer for the consumer is set to the same size as the client's.
        """

        last_state_time = time.time()

        client = await get_client_from_context(context)
        if client is None:
            logging.error("Received consumption request with missing or unknown client id")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Client not found or not given")

        buffer_limit = request.buffer_limit or request.max_rate
        assumed_client_buffer_amount = float(request.current_buffer_amount) or 0.0
        max_rate = request.max_rate

        resource = Resource.get(request.resource_id)
        if resource is None:
            logging.error(f"Received production from client {client} with unknown resource {request.resource_id}")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Unknown resource")

        event = asyncio.Event()
        try:
            consumer = await client.add_consumer(request.consumer_id, resource, buffer_limit, max_rate, event)
        except ValueError as e:
            logging.error(f"Failed to add consumer for consumption request for {resource} from {client}: {e}")
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, f"Failed to add consumer: {e}")

        logger.info(f"Starting sending {resource} to client {client} for consumer {consumer}")

        # maybe there is already something available - set event initially
        event.set()

        try:
            while True:
                # calculate how much should currently be in the client buffer
                t = time.time()
                assumed_client_buffer_amount -= ((t - last_state_time) / 60) * max_rate
                assumed_client_buffer_amount = max(assumed_client_buffer_amount, 0)
                last_state_time = t

                # wait until the client buffer drops below 25%
                await asyncio.sleep(calculate_time_until_buffer_at_25(
                    last_state_time,
                    assumed_client_buffer_amount,
                    buffer_limit,
                    max_rate
                ))

                # try to fill client buffer up to 75% (assuming currently at 25%)
                amount_to_75 = buffer_limit * 0.75 - max(assumed_client_buffer_amount - ((time.time() - last_state_time) / 60) * max_rate, 0)
                amount = await consumer.remove(round(amount_to_75))
                assumed_client_buffer_amount += amount

                if amount > 0:
                    # Send the amount to the client
                    yield virdi_pb2.ResourceProduction(amount=amount)
                else:
                    # Wait until resources are available once more
                    await event.wait()
                    event.clear()
        finally:
            # TODO: different logic for consumer is full (keep buffer) and consumer is removed (remove buffer)
            logger.info(f"Stopping sending {resource} to client {client} for consumer {consumer}")
            await client.remove_consumer(consumer.id)

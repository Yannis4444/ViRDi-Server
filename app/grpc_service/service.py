import asyncio
import logging
from typing import AsyncIterator

import grpc

import app.grpc_service.proto.virdi_pb2 as pb2
import app.grpc_service.proto.virdi_pb2_grpc as pb2_grpc
from app.grpc_service.proto import virdi_pb2

logger = logging.getLogger(__name__)


class MyServiceServicer(pb2_grpc.VirdiServicer):
    async def OfferProduction(self, request: pb2.ProductionOffer, context: grpc.ServicerContext) -> AsyncIterator[pb2.ProductionRequest]:
        """
        A client offers the production of a resource, the server answers whenever the resource is needed
        """

        client_id = dict(context.invocation_metadata()).get("client-id")
        resource_id = request.resource_id

        logger.info(f"Client {client_id} started offering {resource_id}")

        try:
            while True:
                await asyncio.sleep(1)
                # TODO: wait for some event to signal the need for the resource
                logger.info(f"Sending production request for {resource_id} to {client_id}")
                yield pb2.ProductionRequest()
        finally:
            logger.info(f"Client {client_id} stopped offering {resource_id}")

    async def Produce(self, request_iterator: AsyncIterator[pb2.ResourceProduction], context: grpc.ServicerContext) -> pb2.ProductionResponse:
        """
        A client sends resources in a stream
        """

        client_id = dict(context.invocation_metadata()).get("client-id")

        first_message = await anext(request_iterator)
        resource_id = first_message.init_info.resource_id

        logger.info(f"Client {client_id} started sending {resource_id}")

        async for request in request_iterator:
            amount = request.amount
            logger.info(f"Client {client_id} sent {amount} {resource_id}")

        logger.info(f"Client {client_id} stopped sending {resource_id}")

        return virdi_pb2.ProductionResponse()
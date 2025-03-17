import logging

import grpc
import virdi.grpc_service.proto.virdi_pb2_grpc as pb2_grpc
from virdi.grpc_service.service import MyServiceServicer

logger = logging.getLogger(__name__)


async def serve():
    """Starts the async gRPC server."""
    server = grpc.aio.server()
    pb2_grpc.add_VirdiServicer_to_server(MyServiceServicer(), server)
    server.add_insecure_port("[::]:50051")
    logger.info("gRPC Server running on port 50051...")

    await server.start()
    # await server.wait_for_termination()
    return server

async def stop(server):
    logger.info("Stopping gRPC Server")
    await server.stop(grace=True)
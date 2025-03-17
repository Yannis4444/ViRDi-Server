import asyncio
import logging
import signal
from asyncio import gather

from virdi.core.config import load_config
from virdi.grpc_service import server as server
from virdi.metrics.metrics import write_metrics, metrics_shutdown_event

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(name)-32s %(message)s"
)

logger = logging.getLogger("app")

load_config("virdi/config/")


async def main():
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def shutdown():
        logger.info("shutting down")
        shutdown_event.set()

    """Main async function that starts writer and handles signal events."""
    # Register signal handlers for graceful shutdown
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, shutdown)
    except NotImplementedError:
        logger.warning("Failed to register shutdown handler - graceful shutdown not possible")

    grpc_server = await server.serve()
    metrics_task = asyncio.create_task(write_metrics())

    await shutdown_event.wait()

    metrics_shutdown_event.set()
    await server.stop(grpc_server)

    await gather(
        metrics_task
    )


if __name__ == "__main__":
    asyncio.run(main())

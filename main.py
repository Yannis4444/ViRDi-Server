import asyncio
import logging
from virdi.core.config import load_config
from virdi.grpc_service.server import serve

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(name)-32s %(message)s"
)

logger = logging.getLogger("app")

load_config("virdi/config/")

try:
    asyncio.run(serve())
except KeyboardInterrupt:
    print("Shutting down server.")

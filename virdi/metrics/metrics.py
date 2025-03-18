import asyncio
import logging
import os
import time
from datetime import datetime, timezone

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

logger = logging.getLogger(__name__)

# Async queue for metrics
_metrics_queue = asyncio.Queue()

metrics_shutdown_event = asyncio.Event()


async def enqueue_metric(measurement: str, tags: dict, fields: dict):
    """Push a metric to the queue."""
    await _metrics_queue.put((measurement, tags, fields))


async def production_metric(
        client_id: str,
        resource_id: str,
        amount: int
):
    """
    Adds a production metric

    :param client_id: The identifier of the client
    :param resource_id: The identifier of the resource
    :param amount: The amount produced
    """

    await _metrics_queue.put({
        "measurement": "production",
        "tags": {
            "client_id": client_id,
            "resource_id": resource_id,
        },
        "fields": {
            "amount": amount
        },
        "time": datetime.fromtimestamp(time.time(), tz=timezone.utc).isoformat()
    })


async def write_metrics():
    """Background task to consume queue and write metrics in batches."""

    # InfluxDB settings
    influx_url = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
    influx_token = os.getenv("INFLUXDB_TOKEN", "")
    influx_org = os.getenv("INFLUXDB_ORG", "virdi")
    influx_bucket = os.getenv("INFLUXDB_BUCKET", "virdi_metrics")
    flush_interval = int(os.getenv("METRICS_FLUSH_INTERVAL", 10))
    batch_size = int(os.getenv("METRICS_BATCH_SIZE", 500))

    logger.info("Starting writing metrics...")
    async with InfluxDBClientAsync(url=influx_url, token=influx_token, org=influx_org, enable_gzip=True, username="admin") as client:
        write_api = client.write_api()
        batch = []
        last_write = time.time()

        while not metrics_shutdown_event.is_set():
            try:
                try:
                    point = await asyncio.wait_for(_metrics_queue.get(), timeout=max((last_write + flush_interval) - time.time(), 0))
                    batch.append(point)
                except TimeoutError:
                    pass

                if len(batch) >= batch_size or (last_write + flush_interval) <= time.time():
                    logger.debug("Writing metrics")
                    try:
                        await write_api.write(influx_bucket, influx_org, batch)
                        batch.clear()
                        last_write = time.time()
                    except:
                        logger.exception("Error writing metrics")
                        await asyncio.sleep(10)
            except asyncio.TimeoutError:
                logger.info("Stopping writing metrics")
                if batch:
                    await write_api.write(influx_bucket, influx_org, batch)
                    batch.clear()

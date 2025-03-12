"""
Different kind of notifiers used to notify consumers about new resources.
"""
import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)


class Notifier:
    """
    Abstract base class for all notifiers.

    Using `async with notifier` will lock the notifier to only send one notification at a time.
    This is necessary to correctly handle multiple notifications that might arrive simultaneously.
    Otherwise, resources might be consumed multiple times.
    """

    type = ""

    def __init__(self, config: dict):
        """
        Creates a new notifier with the config given by the request

        :param config: The config
        """

        self._config = config

        self._lock = asyncio.Lock()

    def __repr__(self):
        return f"Notifier({self.type}, config={self._config})"

    def __str__(self):
        return f"{self.type} notifier"

    async def __aenter__(self) -> 'AsyncResource':
        """
        Acquire the lock to only notify one at a time.
        """

        await self._lock.acquire()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Releases the lock used to only notify one at a time.
        """
        self._lock.release()

    async def notify(self, amount: int, consumer_id: str) -> int:
        """
        Abstract method that notifies the actual client for the consumer about new resources.

        notify has to return the amount that was actually consumed which will be taken from the buffer once returned.

        :param amount: The available amount.
        :param consumer_id: The id of the consumer.
        :return: The amount actually consumed.
        """

        raise NotImplementedError("notify not implemented")


class DebugNotifier(Notifier):
    """
    Used for debug purposes.

    Will consumer everything and print consumed amounts
    """

    type = "debug"

    async def notify(self, amount: int, consumer_id: str) -> int:
        """
        Debug notify that will always consume everything and print the consumed amount

        :param amount: The available amount.
        :param consumer_id: The id of the consumer.
        :return: The amount actually consumed.
        """

        logger.info(f"Debug Notifier for {consumer_id} consumed {amount}, config={self._config}")

        return amount


class HttpPostNotifier(Notifier):
    """
    Will send a http post request to a configured url.

    The HTTP Response is expected to contain the actually consumed amount.

    **Configuration**
    - `url`: The URL to make the request to.
      Can Include `{{ consumer_id }}` which will be filled with the consumer_id
    - `Content-Type`: How the data should be sent.
      The following Options are available
      - `application/json` (default): Will send the data as a JSON object.
         Example: `{"amount": 42, "consumer_id": "abc123"}`
      - `text/plain`: Will send just the amount as a string.
         Example: `42`
    - `Accept`: How the data is structured in the response.
      The following Options are available
      - `application/json` (default): Will expect the data as a JSON object.
         Example: `{"amount": 17}`
      - `text/plain`: Will expect the amount as a string.
         Example: `17`
    """

    type = "http_post"

    def __init__(self, config: dict):
        super().__init__(config)

        self._url = config.get("url")
        self._content_type = config.get("Content-Type", "application/json")
        self._accept = config.get("Accept", "application/json")

        if self._url is None:
            raise ValueError("Missing url in http_post notifier config")

        if self._content_type not in ["application/json", "text/plain"]:
            raise ValueError(f"Invalid Content-Type in http_post notifier config: {self._content_type}")

        if self._accept not in ["application/json", "text/plain"]:
            raise ValueError(f"Invalid Accept in http_post notifier config: {self._accept}")

    async def notify(self, amount: int, consumer_id: str) -> int:
        """
        Debug notify that will always consume everything and print the consumed amount

        :param amount: The available amount.
        :param consumer_id: The id of the consumer.
        :return: The amount actually consumed.
        """

        # TODO: error handling

        async with httpx.AsyncClient() as client:
            if self._content_type == "application/json":
                response = await client.post(
                    self._url,
                    json={
                        "amount": amount,
                        "consumer_id": consumer_id
                    }
                )
            elif self._content_type == "text/plain":
                response = await client.post(
                    self._url,
                    content=str(amount),
                    headers={"Content-Type": "text/plain"}
                )
            response.raise_for_status()

            if self._accept == "application/json":
                data = response.json()
                amount = data["amount"]
            elif self._accept == "text/plain":
                amount = int(response.text)

            return amount


notifier_classes = {cls.type: cls for cls in Notifier.__subclasses__() if cls.type}


def get_notifier_class(notifier_type) -> type[Notifier] | None:
    """
    Returns the notifier class for the given type

    :param notifier_type: The type of the notifier.
    :return: A matching notifier
    """

    return notifier_classes.get(notifier_type)

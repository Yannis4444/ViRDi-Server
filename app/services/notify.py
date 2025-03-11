"""
Different kind of notifiers used to notify consumers about new resources.
"""
import asyncio
import logging

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
        return self.type

    async def __aenter__(self) -> "AsyncResource":
        """
        Acquire the lock to only notify one at a time.
        """

        await self._lock.acquire()
        return self  # Return the instance to allow usage inside the context

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Releases the lock used to only notify one at a time.
        """
        self._lock.release()

    async def notify(self, amount: int) -> int:
        """
        Abstract method that notifies the actual client for the consumer about new resources.

        notify has to return the amount that was actually consumed which will be taken from the buffer once returned.

        :param amount: The available amount.
        :return: The amount actually consumed.
        """

        raise NotImplementedError("notify not implemented")


class DebugNotifier(Notifier):
    """
    Used for debug purposes.

    Will consumer everything and print consumed amounts
    """

    type = "debug"

    async def notify(self, amount: int) -> int:
        """
        Debug notify that will always consume everything and print the consumed amount

        :param amount:
        :return:
        """

        logger.info(f"Debug Notifier consumed {amount}, config={self._config}")

        return amount

notifier_classes = {cls.type: cls for cls in Notifier.__subclasses__() if cls.type}

def get_notifier_class(notifier_type) -> type[Notifier] | None:
    """
    Returns the notifier class for the given type

    :param notifier_type: The type of the notifier.
    :return: A matching notifier
    """

    return notifier_classes.get(notifier_type)
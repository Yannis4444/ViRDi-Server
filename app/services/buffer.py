import asyncio


class Buffer:
    """
    A buffer which can hold a set number of items.
    Used for global resource buffers and consumer buffers.
    """

    def __init__(self, limit: int, initial_amount: int = 0):
        """
        Creates a new buffer

        :param limit: The maximum amount that can be stored in the buffer
        :param initial_amount: The initial amount
        """

        self._limit: int = limit
        self._amount: int = initial_amount

        self._lock = asyncio.Lock()

    def __repr__(self):
        return f"Buffer({self._amount}/{self._limit})"

    def __str__(self):
        return self.__repr__()

    @property
    def limit(self) -> int:
        """
        The limit of the buffer

        :return: The limit
        """

        return self._limit

    @property
    def amount(self) -> int:
        """
        The amount of the buffer

        :return: The amount
        """

        return self._amount

    @property
    def lock(self) -> asyncio.Lock:
        """
        The lock for th buffer amount

        :return: The lock
        """

        return self._lock

    async def add(self, amount, lock=True) -> bool:
        """
        Adds the given amount to the buffer.

        Once the buffer is full, the full amount will still be added,
        but False will be returned to signal that nothing more should be added.

        If the buffer is already locked manually, lock can be set to False.

        :param amount: The amount to add
        :param lock: If the amount should be locked during the operation
        :return: True if the buffer is not yet fully filled, False otherwise
        """

        if lock:
            async with self._lock:
                self._amount += amount
                return self._amount < self._limit
        else:
            self._amount += amount
            return self._amount < self._limit

    async def remove(self, amount, lock=True) -> int:
        """
        Removes the given amount from the buffer.
        If the buffer is completely empty, the return value will be less than the set amount.

        If the buffer is already locked manually, lock can be set to False.

        :param amount: The amount to remove
        :param lock: If the amount should be locked during the operation
        :return: The amount actually removed
        """

        if lock:
            async with self._lock:
                actual_amount = min(amount, self._amount)
                self._amount -= actual_amount
                return actual_amount
        else:
            actual_amount = min(amount, self._amount)
            self._amount -= actual_amount
            return actual_amount

    async def remove_all(self, lock=True) -> int:
        """
        Removes everything from the buffer.

        If the buffer is already locked manually, lock can be set to False.

        :param lock: If the amount should be locked during the operation
        :return: The amount actually removed
        """

        if lock:
            async with self._lock:
                return await self.remove(self.amount, lock=False)
        else:
            return await self.remove(self.amount, lock=False)

    def is_full(self) -> bool:
        """
        Checks if the buffer is full.

        :return: True if the buffer is full
        """

        return self._amount >= self._limit
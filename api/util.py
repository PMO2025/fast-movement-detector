import asyncio
from typing import Generic, TypeVar
from weakref import WeakSet

T = TypeVar("T")


class StateStream(Generic[T]):
    _END = {}

    def __init__(self, value: T):
        self.value = value
        self.closed = False
        self.queues = WeakSet[asyncio.Queue]()

    def get(self):
        return self.value

    def set(self, value: T):
        if self.closed:
            return

        self.value = value
        for queue in self.queues:
            queue.put_nowait(value)

    def close(self):
        if self.closed:
            return

        self.closed = True
        for queue in self.queues:
            queue.put_nowait(StateStream._END)

    async def __aiter__(self):
        if self.closed:
            yield self.value
            return

        queue = asyncio.Queue()
        self.queues.add(queue)

        yield self.value

        while True:
            value = await queue.get()
            if value is StateStream._END:
                break

            yield value

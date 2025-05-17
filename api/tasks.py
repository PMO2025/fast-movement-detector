from __future__ import annotations

import asyncio
from dataclasses import dataclass
import threading
from time import sleep

import cv2
import janus

from .util import StateStream

from src.model import Model
from src.util import read_video, VideoWriter


@dataclass
class Enqueued:
    position: int

    def to_dict(self):
        return {"status": "enqueued", "position": self.position}


@dataclass
class Pending:
    progress: float

    def to_dict(self):
        return {"status": "pending", "progress": self.progress}


@dataclass
class Failed:
    error: str

    def to_dict(self):
        return {"status": "failed", "error": self.error}


@dataclass
class Completed:
    def to_dict(self):
        return {"status": "completed"}


Status = Enqueued | Pending | Failed | Completed


@dataclass
class Payload:
    in_path: str
    out_path: str


@dataclass
class Task:
    id: int
    payload: Payload
    status_stream: StateStream[Status]


class Worker:
    def __init__(self, manager: Manager):
        self.manager = manager

    async def run(self):
        self.input = janus.Queue()
        self.output = janus.Queue()

        self.thread = threading.Thread(target=self.target)
        self.thread.start()

        while True:
            task = await self.manager.pop_queue()

            await self.input.async_q.put(task)

            while True:
                status = await self.output.async_q.get()
                task.status_stream.set(status)

                if not isinstance(status, Pending):
                    task.status_stream.close()
                    break

    def target(self):
        self.init()

        while True:
            task = self.input.sync_q.get()

            try:
                it = self.infer(task.payload)
                while True:
                    try:
                        progress = next(it)
                        self.output.sync_q.put(Pending(progress))
                    except StopIteration as e:
                        self.output.sync_q.put(Completed())
                        break

            except Exception as e:
                self.output.sync_q.put(Failed(str(e)))

    def init(self):
        self.model = Model(processing_shape=(384, 640))

    def infer(self, payload: Payload):
        video, fps = read_video(payload.in_path)

        preds = self.model.infer(video, fps=fps)
        vis = self.model.visualize(preds)

        writer = VideoWriter(payload.out_path, "webm", fps)

        for i, vis_frame in enumerate(vis):
            writer.write(vis_frame)
            yield i / len(video)

        writer.close()


class Manager:
    queue: list[Task]
    tasks: dict[int, Task]

    def __init__(self, n_workers: int):
        self.n_workers = n_workers

        self.enqueue_event = asyncio.Event()
        self.queue = []
        self.tasks = {}
        self.next_id = 0

    async def pop_queue(self):
        if len(self.queue) > 0:
            task = self.queue.pop(0)
        else:
            while True:
                await self.enqueue_event.wait()
                self.enqueue_event.clear()

                if len(self.queue) > 0:
                    task = self.queue.pop(0)
                    break

        task.status_stream.set(Pending(0))

        for i, enq in enumerate(self.queue):
            enq.status_stream.set(Enqueued(i))

        return task

    def add_task(self, payload) -> int:
        id = self.next_id
        self.next_id += 1

        task = Task(
            id=id,
            payload=payload,
            status_stream=StateStream(Enqueued(len(self.queue)))
        )

        self.tasks[id] = task
        self.queue.append(task)

        self.enqueue_event.set()

        return id

    def get_task(self, id: int):
        if id in self.tasks:
            return self.tasks[id]
        else:
            return None

    async def run(self):
        workers = [
            asyncio.create_task(Worker(self).run())
            for _ in range(self.n_workers)
        ]

        for worker in workers:
            await worker

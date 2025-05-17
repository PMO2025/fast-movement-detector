import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
import json
import os

import aiofiles
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette import EventSourceResponse

from .tasks import Completed, Manager, Payload


def sse_response(gen):
    async def json_gen():
        async for event in gen:
            yield f"{json.dumps(event)}\n\n"

    return StreamingResponse(json_gen(), media_type="text/event-stream")


def create_api(allow_cors=False):
    in_dir = "./temp/input"
    out_dir = "./temp/output"

    manager = None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal manager

        manager = Manager(1)
        asyncio.create_task(manager.run())

        yield

    api = FastAPI(lifespan=lifespan)

    if allow_cors:
        origins = ["*"]

        api.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @api.get("/status")
    async def status(id: int):
        task = manager.get_task(id)

        if task is None:
            return JSONResponse({
                "status": "error",
                "error": "no such task"
            }, 404)

        async def events():
            try:
                async for ev in task.status_stream:
                    yield ev.to_dict()

            except Exception as e:
                yield {
                    "status": "error",
                    "error": str(e)
                }

        async def gen():
            async for ev in events():
                yield {"data": json.dumps(ev)}

        return EventSourceResponse(gen())

    @api.post("/upload")
    async def upload(video: UploadFile):
        name = datetime.now().strftime(f"%Y-%d-%m_%H_%M_%S-%f")
        in_path = os.path.join(in_dir, name)
        out_path = os.path.join(out_dir, name + ".webm")

        async with aiofiles.open(in_path, "wb") as out:
            while content := await video.read(4096):
                await out.write(content)

        id = manager.add_task(Payload(
            in_path=in_path,
            out_path=out_path
        ))

        return {
            "status": "success",
            "id": id
        }

    @api.get("/download")
    async def download(id: int):
        task = manager.get_task(id)

        if task is None:
            return JSONResponse({
                "status": "error",
                "error": "no such task"
            }, 404)

        status = task.status_stream.get()

        if not isinstance(status, Completed):
            return JSONResponse({
                "status": "error",
                "error": "task is not completed"
            }, 400)

        return FileResponse(task.payload.out_path, media_type="video/webm")

    return api

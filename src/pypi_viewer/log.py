import logging
import time

from fastapi import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


def configure_logger():
    log_format = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(log_format)
    root_logger.addHandler(handler)
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.disabled = True


class LoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)

        async def inner_send(message: Message):
            if message["type"] == "http.response.start":
                start_time = time.perf_counter()
                await send(message)
                end_time = time.perf_counter()
                process_time = end_time - start_time
                logger.info(
                    f"{request.method} {request.url}: {message["status"]} in {process_time:.2f} ms"
                )
            else:
                await send(message)

        await self.app(scope, receive, inner_send)

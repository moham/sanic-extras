import logging
import uuid
from typing import Callable, Optional
from contextvars import ContextVar
from sanic.request import Request


request_id = ContextVar('request_id', default="none")


class AddRequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        return True


class Logging:
    def __init__(
        self,
        id_generator: Optional[Callable[[], str]] = None
    ) -> None:
        self._id_generator = id_generator or (lambda: uuid.uuid4().hex[:12])

    def get_logger(self, name: str, *args, **kwargs) -> logging.Logger:
        logger = logging.getLogger(name, *args, **kwargs)
        logger.addFilter(AddRequestIdFilter())
        return logger

    async def sanic_middleware(self, request: Request) -> None:
        id_ = self._id_generator()
        request.ctx.request_id = id_
        request_id.set(id_)

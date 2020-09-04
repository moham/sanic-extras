import functools
from typing import Optional, Awaitable
from pydantic import BaseModel, ValidationError
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic.exceptions import InvalidUsage, ServerError

try:
    from ujson import loads as json_loads
except ImportError:
    from json import loads
    json_loads = functools.partial(loads, separators=(",", ":"))


async def json_data_validation(
        request_model: Optional[BaseModel] = None,
        response_model: Optional[BaseModel] = None
) -> HTTPResponse:
    async def validation_wraper(func: Awaitable):
        @functools.wraps(func)
        async def check_validation(request: Request, *args, **kwargs):
            if request_model is not None:
                try:
                    request.ctx.model = request_model(**request.json)
                except (InvalidUsage, ValidationError):
                    raise InvalidUsage("Request data validation error")
            
            response: HTTPResponse = await func(request, *args, **kwargs)
            
            if response_model is not None:
                try:
                    response_body = response.body_dict
                except AttributeError:
                    response_body = json_loads(response.body)
 
                try:
                    response_model(**response_body)
                except ValidationError:
                    raise ServerError("Internal server error")

            return response
        return check_validation
    return validation_wraper

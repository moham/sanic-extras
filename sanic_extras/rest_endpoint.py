import functools
from typing import Optional, Awaitable, List, Dict
from pydantic import BaseModel, ValidationError, validate_model
from sanic.request import Request
from sanic.response import json as json_response
from sanic.response import empty as empty_response
from sanic.exceptions import InvalidUsage, ServerError, Unauthorized, Forbidden


class RestEndpoint:
    def __init__(
        self,
        *,
        login_required: bool = False,
        required_scopes: List[str] = [],
        request_model: Optional[BaseModel] = None,
        response_model: Optional[BaseModel] = None,
        response_headers: Optional[Dict[str, str]] = None,
        response_status: int = 200
    ) -> None:
        self.login_required = login_required
        self.required_scopes = required_scopes
        self.request_model = request_model
        self.response_model = response_model
        self.response_headers = response_headers
        self.response_status = response_status

    def check_auth(self, request: Request) -> None:
        try:
            if request.ctx.request_user is None:
                raise Unauthorized("Unauthorized")

            if self.required_scopes:
                if not (
                    set(self.required_scopes) & 
                    set(request.ctx.request_user.scopes)
                ):
                    raise Forbidden("Forbidden")
        except AttributeError:
            raise Unauthorized("Unauthorized")

    def check_request_model(self, request: Request) -> None:
        try:
            request.ctx.request_data = self.request_model(**request.json)
        except ValidationError as e:
            raise InvalidUsage(e.json())

    def check_response_model(self, response: Dict) -> None:
        _, _, validation_error = validate_model(self.response_model, response)

        if validation_error:
            raise ServerError("Bad response")

    def __call__(self, handler: Awaitable) -> Awaitable:
        @functools.wraps(handler)
        async def rest_endpoint_handler(request: Request, *args, **kwargs):
            if self.login_required:
                self.check_auth(request)

            if self.request_model:
                self.check_request_model(request)

            response: Optional[Dict] = await handler(request, *args, **kwargs)
            
            if self.response_model:
                if response is None:
                    raise ServerError("Bad response")
                self.check_response_model(response)

            if response is None:
                return empty_response(
                    status=self.response_status,
                    headers=self.response_headers
                )
            else:  
                return json_response(
                    response,
                    status=self.response_status,
                    headers=self.response_headers
                )

        return rest_endpoint_handler

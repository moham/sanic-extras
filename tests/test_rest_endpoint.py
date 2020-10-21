import unittest
import asyncio
from typing import List
from dataclasses import dataclass
from sanic.response import HTTPResponse
from sanic.exceptions import InvalidUsage, ServerError, Unauthorized, Forbidden
from pydantic import BaseModel
from sanic_extras import RestEndpoint


class RSModel(BaseModel):
    level: int


@dataclass
class CTX: pass


@dataclass
class User:
    username: str
    scopes: List[str]


class Request:
    ctx = CTX()
    json = {}


class TestRestEndpoint(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()

    def test_request_validation(self) -> None:
        request = Request()

        @RestEndpoint(request_model=RSModel)
        async def endpoint(request, *args, **kwargs) -> None:
            pass

        request.json = {"level": "wrong"}
        with self.assertRaises(InvalidUsage):
            self.loop.run_until_complete(endpoint(request))

        request.json = {"level": 1}
        self.loop.run_until_complete(endpoint(request))

    def test_response_validation(self) -> None:
        request = Request()

        @RestEndpoint(response_model=RSModel)
        async def endpoint(*args, **kwargs) -> None:
            return {"level": 1}
        
        @RestEndpoint(response_model=RSModel)
        async def endpoint(*args, **kwargs) -> None:
            return {"level": "wrong"}
        
        with self.assertRaises(ServerError):
            self.loop.run_until_complete(endpoint(request))
        
        @RestEndpoint(response_model=RSModel)
        async def endpoint(request, *args, **kwargs) -> None:
            pass
        
        with self.assertRaises(ServerError):
            self.loop.run_until_complete(endpoint(request))

    def test_request_auth(self) -> None:
        request = Request()
        user = User(username="test", scopes=["read_write"])

        @RestEndpoint(login_required=True)
        async def endpoint(*args, **kwargs) -> None:
            pass

        with self.assertRaises(Unauthorized):
            self.loop.run_until_complete(endpoint(request))

        request.ctx.request_user = user
        self.loop.run_until_complete(endpoint(request))

        @RestEndpoint(login_required=True, required_scopes=["readonly"])
        async def endpoint(*args, **kwargs) -> None:
            pass

        with self.assertRaises(Forbidden):
            self.loop.run_until_complete(endpoint(request))
        
        @RestEndpoint(login_required=True, required_scopes=["read_write"])
        async def endpoint(*args, **kwargs) -> None:
            pass

        self.loop.run_until_complete(endpoint(request))

        @RestEndpoint(login_required=True, required_scopes=["read_write", "ro"])
        async def endpoint(*args, **kwargs) -> None:
            pass

        self.loop.run_until_complete(endpoint(request))
    
    def test_response_headers(self) -> None:
        request = Request()
        success_headers = {"X-TEST": "Success"}
        failed_headers = {"X-TEST": "Failed"}

        @RestEndpoint(response_headers=success_headers)
        async def endpoint(*args, **kwargs) -> None:
            pass

        response: HTTPResponse = self.loop.run_until_complete(endpoint(request))
        self.assertTrue(
            set(success_headers.items()).issubset(set(response.headers.items()))
        )
        self.assertFalse(
            set(failed_headers.items()).issubset(set(response.headers.items()))
        )

    def test_response_status(self) -> None:
        request = Request()
        success_status = 200
        failed_status = 400

        @RestEndpoint(response_status=success_status)
        async def endpoint(*args, **kwargs) -> None:
            pass

        response: HTTPResponse = self.loop.run_until_complete(endpoint(request))
        self.assertEqual(response.status, success_status)
        
        with self.assertRaises(AssertionError):
            self.assertEqual(response.status, failed_status)

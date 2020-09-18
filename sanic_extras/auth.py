from typing import List, Optional, Dict, Union, Type, Callable
from datetime import datetime, timedelta
import jwt
from sanic.request import Request
from pydantic import BaseModel, ValidationError


class BaseUserAuthModel(BaseModel):
    scopes: List[str] = []


class BaseUserGetTokenModel(BaseModel):
    access_token: str
    refresh_token: str
    access_ttl: int
    refresh_ttl: int


class OAuth2HTTP:
    __slots__ = (
        '_http_request',
        '_token_type',
        '_http_auth_header',
        '_token'
    )

    def __init__(
        self,
        http_request: Request,
        *,
        token_type: Optional[str] = None,
        http_auth_header: Optional[str] = None
    ) -> None:
        self._http_request = http_request
        self._token_type = token_type or "Bearer"
        self._http_auth_header = http_auth_header or "Authorization"
        self._token: Optional[str] = None

    def _extract_token(self) -> Optional[str]:
        if self._http_auth_header not in self._http_request.headers:
            return None
        
        content: List[str] = self._http_request[self._http_auth_header].split()

        if len(content) != 2 or content[0].title() != self._token_type:
            return None

        return content[1]

    @property
    def token(self) -> Optional[str]:
        if self._token is None:
            self._token = self._extract_token()
        return self._token


class JWT():
    def __init__(
        self,
        algorithm: str,
        *,
        secret_key: Optional[str] = None,
        private_key: Optional[bytes] = None,
        public_key: Optional[bytes] = None,
        subject: Optional[str] = None,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        not_before: Optional[datetime] = None,
        issued_at: Optional[str] = None,
        time_to_live: Optional[timedelta] = None,
        payload_model: Optional[Type[BaseUserAuthModel]] = None,
        filter: Optional[Callable[[Dict], Dict]] = None,
        token_type: Optional[str] = None,
        http_auth_header: Optional[str] = None
    ) -> None:
        self._algorithm = algorithm
        self._secret_key = secret_key
        self._private_key = private_key
        self._public_key = public_key
        self._subject = subject or ""
        self._issuer = issuer or ""
        self._audience = audience or ""
        self._not_before = not_before
        self._issued_at = issued_at
        self._time_to_live = time_to_live or timedelta(hours=1)
        self._payload_model = payload_model or BaseUserAuthModel
        self._filter = filter
        self._token_type = token_type
        self._http_auth_header = http_auth_header

        self._encode_key = None
        self._decode_key = None
        self._payload_key = "payload"

        self._HS_ALGORITHMS = ['HS256', 'HS384', 'HS512']
        self._RS_ALGORITHMS = ['RS256', 'RS384', 'RS512']

        if self._algorithm in self._HS_ALGORITHMS:
            if self._secret_key is None:
                raise AttributeError(
                    f"secret key must be set for "
                    f"{','.join(self._HS_ALGORITHMS)} algorithms."
                )
            self._encode_key = self._secret_key
            self._decode_key = self._secret_key
        elif self._algorithm in self._RS_ALGORITHMS:
            if not (self._private_key or self._public_key):
                raise AttributeError(
                    f"private or public key must be set for "
                    f"{','.join(self._RS_ALGORITHMS)} algorithms."
                )
            self._encode_key = self._private_key
            self._decode_key = self._public_key
        else:
            raise AttributeError(
                f"unknown algorithm '{self._algorithm}'. "
                f"must be one of the "
                f"{','.join(self._HS_ALGORITHMS + self._RS_ALGORITHMS)}."
            )

    def token(
        self,
        payload_dict: Optional[Dict] = None,
        payload_model: Optional[BaseModel] = None,
    ) -> Optional[str]:
        now = datetime.utcnow()
        payload = {
            'sub': self._subject,
            'iss': self._issuer,
            'aud': self._audience,
            'iat': self._issued_at or now,
            'nbf': self._not_before or now,
            'exp': now + self._time_to_live
        }

        if payload_dict is not None:
            payload[self._payload_key] = payload_dict
        elif payload_model is not None:
            payload[self._payload_key] = payload_model.dict()
        else:
            payload[self._payload_key] = {}
        
        try:
            token = jwt.encode(
                payload=payload,
                key=self._decode_key,
                algorithm=self._algorithm)
        except Exception:
            token = None

        return token

    def payload(
        self,
        token: str,
        *,
        payload_model: Optional[BaseModel] = None
    ) -> Optional[Union[Dict, BaseModel]]:
        try:
            payload = jwt.decode(
                jwt=token,
                key=self._decode_key,
                issuer=self._issuer,
                audience=self._audience,
                algorithms=[self._algorithm]
            )
        except Exception:
            return None
        
        if self._filter:
            try:
                payload = self._filter(payload)
            except Exception:
                return None
        else:
            try:
                payload = payload[self._payload_key]
            except KeyError:
                return None

        if payload_model:
            try:
                payload = payload_model(**payload)
            except ValidationError:
                return None

        return payload

    async def decoder_middleware(self, request: Request) -> None:
        oauth2_http = OAuth2HTTP(
            request,
            token_type=self._token_type,
            http_auth_header=self._http_auth_header
        )

        if oauth2_http.token:
            request.ctx.request_user = self.payload(
                token=oauth2_http.token,
                payload_model=self._payload_model
            )
        else:
            request.ctx.request_user = None

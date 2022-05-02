from starlette.requests import Request
from starlette.responses import Response
from .endpoint import endpoint
import httpx

DESTINATION_ENDPOINT:str = endpoint

async def app(scope, receive, send):
    request = Request(scope, receive)
    url = DESTINATION_ENDPOINT + request.url.path
    content = httpx.get(url)
    response = Response(content.text, media_type="application/json")
    await response(scope, receive, send)

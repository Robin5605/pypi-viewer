from functools import cache
import httpx


@cache
def httpx_client() -> httpx.Client:
    return httpx.Client()

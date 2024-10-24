from functools import lru_cache
import logging
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Response
import httpx
from tempfile import TemporaryFile
from pypi_viewer.distribution import Distribution, TarGz, Zip
from pypi_viewer.schemas import File
from pypi_viewer.constants import pypi_viewer_settings
from pypi_viewer.log import LoggingMiddleware, configure_logger
from pypi_viewer.dependencies import httpx_client

app = FastAPI()

configure_logger()


ZIP_EXTENSIONS = (".whl", ".egg", ".zip")
TAR_EXTENSIONS = (".tar.gz",)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=pypi_viewer_settings.CACHE_SIZE)
def download_distribution(url: str, http_client: httpx.Client) -> Distribution:
    """Download a distribution from the given URL to a tempfile in a streaming manner."""
    fp = TemporaryFile()
    with http_client.stream("GET", url) as r:
        r.raise_for_status()
        for chunk in r.iter_bytes(chunk_size=pypi_viewer_settings.CHUNK_SIZE):
            fp.write(chunk)
    if url.endswith(TAR_EXTENSIONS):
        return TarGz(fp)
    elif url.endswith(ZIP_EXTENSIONS):
        return Zip(fp)
    else:
        raise ValueError(f"{url} is not recognized as a tar file or a zip file.")


@app.get("/packages/{first}/{second}/{rest}/{distname}/")
def list_distribution_files(
    first: str,
    second: str,
    rest: str,
    distname: str,
    http_client: Annotated[httpx.Client, Depends(httpx_client)],
) -> list[File]:
    url = f"https://files.pythonhosted.org/packages/{first}/{second}/{rest}/{distname}"
    try:
        distribution = download_distribution(url, http_client)
    except httpx.HTTPStatusError as exception:
        status_code = exception.response.status_code
        logger.warn(f"Unable to download {url}, server returned {status_code}")
        raise HTTPException(
            status_code,
            detail="Unable to get files from pythonhosted.org",
        )
    except ValueError as exception:
        raise HTTPException(400, detail=str(exception))

    return distribution.get_files()


@app.get("/packages/{first}/{second}/{rest}/{distname}/{filepath:path}")
def get_file_content(
    first: str,
    second: str,
    rest: str,
    distname: str,
    filepath: str,
    http_client: Annotated[httpx.Client, Depends(httpx_client)],
):
    url = f"https://files.pythonhosted.org/packages/{first}/{second}/{rest}/{distname}"
    try:
        distribution = download_distribution(url, http_client)
    except httpx.HTTPStatusError as exception:
        status_code = exception.response.status_code
        logger.warn(f"Unable to download {url}, server returned {status_code}")
        raise HTTPException(
            exception.response.status_code,
            detail="Unable to get files from pythonhosted.org",
        )

    try:
        content = distribution.get_file_contents(filepath)
        return Response(content=content, media_type="application/octet-stream")
    except FileNotFoundError as exception:
        raise HTTPException(404, detail=str(exception))


app.add_middleware(LoggingMiddleware)

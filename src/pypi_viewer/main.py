from fastapi import FastAPI, HTTPException, Request
import httpx
from httpx import AsyncClient
from zipfile import ZipFile
import tarfile
from tarfile import TarFile
from io import BytesIO
import time
from tempfile import TemporaryFile
from typing import IO, BinaryIO
import shutil

app = FastAPI()

cache: dict[tuple[str, str, str], ZipFile | TarFile] = {}

http_client = AsyncClient()

async def download_file(url: str) -> BinaryIO:
    """Download a file from the given URL to a tempfile in a streaming manner."""
    async with http_client.stream("GET", url) as r:
        r.raise_for_status()
        fp = TemporaryFile()
        async for chunk in r.aiter_bytes():
            fp.write(chunk)
    fp.seek(0)
    return fp

def get_filenames(file: ZipFile | TarFile) -> list[str]:
    if isinstance(file, ZipFile):
        return [i.filename for i in file.infolist() if not i.is_dir()]
    elif isinstance(file, TarFile):
        return [i.name for i in file.getmembers() if not i.isdir()]

@app.get("/project/{name}/{version}/packages/{first}/{second}/{rest}/{distname}")
async def list_distribution_files(name: str, version: str, first: str, second: str, rest: str, distname: str) -> list[str]:
    key = (name, version, distname)
    if file := cache.get(key):
        return get_filenames(file)

    url = f"https://files.pythonhosted.org/packages/{first}/{second}/{rest}/{distname}"
    try:
        fp = await download_file(url)
    except httpx.HTTPStatusError as exception:
        raise HTTPException(exception.response.status_code, detail="Unable to get files from pythonhosted.org")

    if distname.endswith((".whl", ".zip", ".egg")):
        cache[key] = ZipFile(fp)
    elif distname.endswith(".tar.gz"):
        cache[key] = tarfile.open(fileobj=fp, mode="r:gz")
    else:
        raise HTTPException(400, detail="File type is not supported")

    return get_filenames(cache[key])

@app.middleware("http")
async def log_process_time(request: Request, call_next):
    start_time = time.perf_counter_ns()
    response = await call_next(request)
    end_time = time.perf_counter_ns()
    print(f"Time taken: {(end_time - start_time)/1e+6} ms")
    return response

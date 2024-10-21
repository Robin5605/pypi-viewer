from fastapi import FastAPI, HTTPException, Request
import httpx
from httpx import AsyncClient
from zipfile import ZipFile
import tarfile
from tarfile import TarFile
from io import BytesIO
import time

app = FastAPI()

http_client = AsyncClient()

cache: dict[str, ZipFile | TarFile] = {}

@app.get("/project/{name}/{version}/packages/{first}/{second}/{rest}/{distname}")
async def list_distribution_files(name: str, version: str, first: str, second: str, rest: str, distname: str) -> list[str]:
    file = cache.get(distname)
    if isinstance(file, ZipFile):
        return [i.filename for i in file.infolist() if not i.is_dir()]
    elif isinstance(file, TarFile):
        return [i.name for i in file.getmembers() if not i.isdir()]

    url = f"https://files.pythonhosted.org/packages/{first}/{second}/{rest}/{distname}"
    try:
        response = await http_client.get(url)
        response.raise_for_status()
    except httpx.HTTPStatusError as exception:
        raise HTTPException(exception.response.status_code, detail="Unable to get files from pythonhosted.org")

    f = BytesIO(response.content)

    if distname.endswith((".whl", ".zip", ".egg")):
        zip = ZipFile(f)
        cache[distname] = zip
        return [i.filename for i in zip.infolist() if not i.is_dir()]
    elif distname.endswith(".tar.gz"):
        tar = tarfile.open(fileobj=f, mode="r:gz")
        cache[distname] = tar
        return [i.name for i in tar.getmembers() if not i.isdir()]
    else:
        raise HTTPException(400, detail="File type is not supported")

@app.middleware("http")
async def log_process_time(request: Request, call_next):
    start_time = time.perf_counter_ns()
    response = await call_next(request)
    end_time = time.perf_counter_ns()
    print(f"Time taken: {(end_time - start_time)/1e+6} ms")
    return response

import httpx
from urllib.parse import urlparse, urlunparse

def main():
    response = httpx.get("https://pypi.org/pypi/tensorflow/2.18.0rc2/json")
    json = response.json()
    for i in json["urls"]:
        url = urlunparse(urlparse(i["url"])._replace(scheme="http", hostname="localhost", port=8000))
        print(url)

        response = httpx.get(url)
        resposne.raise_for_status()


if __name__ == "__main__":
    main()

from collections.abc import Generator
from typing import Protocol, IO
from pypi_viewer.schemas import File
from zipfile import ZipFile
import tarfile
from pypi_viewer.constants import pypi_viewer_settings

DEFAULT_CHUNK_SIZE: int = pypi_viewer_settings.CHUNK_SIZE


class Distribution(Protocol):
    def get_files(self) -> list[File]:
        """Get all the file names and sizes in this distribution."""
        ...

    def get_file_contents(self, path: str) -> bytes:
        """Get the byte contents of a file in this distribution.

        Raises:
            - `FileNotFoundError`: if the path was not found in the distribution or it was a directory
        """
        ...

    def get_file_size(self, path: str) -> int:
        """Get the file size of a file in this distribution.

        Raises:
            - `FileNotFoundError` if the path was not found in the distribution or it was a directory
        """
        ...

    def stream_file_contents(
        self, path: str, *, chunk_size: int = DEFAULT_CHUNK_SIZE
    ) -> Generator[bytes, None, None]:
        """Stream the contents of this file.

        Raises:
            - `FileNotFoundError` if the path was not found in the distribution or it was a directory
        """
        ...


class Zip(Distribution):
    def __init__(self, file: IO[bytes]) -> None:
        self.file = file

    def get_files(self) -> list[File]:
        zip = ZipFile(self.file)
        return [
            File(name=i.filename, size=i.file_size)
            for i in zip.infolist()
            if not i.is_dir()
        ]

    def get_file_contents(self, path: str) -> bytes:
        return b"".join(self.stream_file_contents(path))

    def stream_file_contents(
        self, path: str, *, chunk_size: int = DEFAULT_CHUNK_SIZE
    ) -> Generator[bytes, None, None]:
        zip = ZipFile(self.file)
        try:
            with zip.open(path) as f:
                while b := f.read(chunk_size):
                    yield b
        except KeyError:
            raise FileNotFoundError(f"{path} is not found")

    def get_file_size(self, path: str) -> int:
        zip = ZipFile(self.file)
        try:
            info = zip.getinfo(path)
            if info.is_dir():
                raise KeyError
        except KeyError:
            raise FileNotFoundError(f"{path} is not found")

        return info.file_size


class TarGz(Distribution):
    def __init__(self, file: IO[bytes]) -> None:
        self.file = file

    def get_files(self) -> list[File]:
        self.file.seek(0)
        tar = tarfile.open(fileobj=self.file)
        return [
            File(name=i.name, size=i.size) for i in tar.getmembers() if not i.isdir()
        ]

    def get_file_contents(self, path: str) -> bytes:
        return b"".join(self.stream_file_contents(path))

    def stream_file_contents(
        self, path: str, *, chunk_size: int = DEFAULT_CHUNK_SIZE
    ) -> Generator[bytes, None, None]:
        self.file.seek(0)
        tar = tarfile.open(fileobj=self.file)
        try:
            f = tar.extractfile(path)
        except KeyError:
            raise FileNotFoundError(f"{path} is not found")
        if f is None:
            raise FileNotFoundError(f"{path} is not a file")

        while b := f.read(chunk_size):
            yield b

    def get_file_size(self, path: str) -> int:
        self.file.seek(0)
        tar = tarfile.open(fileobj=self.file)
        try:
            f = tar.getmember(path)
            if f.isdir():
                raise KeyError
        except KeyError:
            raise FileNotFoundError(f"{path} is not found")

        return f.size

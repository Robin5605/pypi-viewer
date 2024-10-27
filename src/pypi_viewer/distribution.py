from typing import Protocol, IO
from pypi_viewer.schemas import File
from zipfile import ZipFile
import tarfile


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
        zip = ZipFile(self.file)
        try:
            with zip.open(path) as f:
                return f.read()
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
        self.file.seek(0)
        tar = tarfile.open(fileobj=self.file)
        try:
            f = tar.extractfile(path)
        except KeyError:
            raise FileNotFoundError(f"{path} is not found")
        if f is None:
            raise FileNotFoundError(f"{path} is not a file")

        return f.read()

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

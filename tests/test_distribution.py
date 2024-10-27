import tarfile
from hypothesis import given
from hypothesis.strategies import binary, lists, text, tuples
from string import ascii_letters, digits
from tempfile import TemporaryFile

from io import BytesIO
from zipfile import ZipFile

from pypi_viewer.distribution import Zip, TarGz

ALPHABET = ascii_letters + digits + "_- "


@given(lists(text(ALPHABET), unique=True))
def test_zipfile_get_filenames(filenames: list[str]):
    with TemporaryFile() as f:
        with ZipFile(f, mode="w") as zip:
            for name in filenames:
                zip.writestr(name, "")

        distribution = Zip(f)
        actual_files = distribution.get_files()

        assert len(actual_files) == len(filenames)
        for file in actual_files:
            assert file.name in filenames


@given(lists(text(ALPHABET), unique=True))
def test_tarfile_get_filenames(filenames: list[str]):
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name in filenames:
            tarinfo = tarfile.TarInfo(name)
            tarinfo.size = 0
            tar.addfile(tarinfo)

    distribution = TarGz(buf)
    actual_files = distribution.get_files()

    assert len(actual_files) == len(filenames)
    for file in actual_files:
        assert file.name in filenames


@given(lists(tuples(text(ALPHABET, min_size=1), binary()), unique_by=lambda x: x[0]))
def test_zipfile_get_size(files: list[tuple[str, bytes]]):
    buf = BytesIO()
    with ZipFile(buf, mode="w") as zip:
        for name, content in files:
            zip.writestr(name, content)

    distribution = Zip(buf)
    for filename, content in files:
        assert distribution.get_file_size(filename) == len(content)


@given(lists(tuples(text(ALPHABET, min_size=1), binary()), unique_by=lambda x: x[0]))
def test_tarfile_get_size(files: list[tuple[str, bytes]]):
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in files:
            info = tarfile.TarInfo(name)
            info.size = len(content)

            tar.addfile(info, BytesIO(content))

    distribution = TarGz(buf)
    for filename, content in files:
        assert distribution.get_file_size(filename) == len(content)


@given(text(ALPHABET, min_size=1), binary(min_size=2))
def test_zipfile_stream_contents(name: str, content: bytes):
    buf = BytesIO()
    with ZipFile(buf, mode="w") as zip:
        zip.writestr(name, content)

    distribution = Zip(buf)
    first_chunk = next(distribution.stream_file_contents(name, chunk_size=1))
    assert len(first_chunk) < len(content)
    assert content.startswith(first_chunk)


@given(text(ALPHABET, min_size=1), binary(min_size=2))
def test_tarfile_stream_contents(name: str, content: bytes):
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(name)
        info.size = len(content)

        tar.addfile(info, BytesIO(content))

    distribution = TarGz(buf)
    first_chunk = next(distribution.stream_file_contents(name, chunk_size=1))
    assert len(first_chunk) < len(content)
    assert content.startswith(first_chunk)

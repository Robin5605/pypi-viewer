import tarfile
from hypothesis import given
from hypothesis.strategies import lists, text
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

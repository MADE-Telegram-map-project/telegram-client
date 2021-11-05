import pytest

from core import Crawler


@pytest.fixture(scope="module")
def crawler() -> Crawler:
    return Crawler()


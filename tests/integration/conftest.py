import os

import pytest
import vcr
from vcr.record_mode import RecordMode


@pytest.fixture(scope="session")
def github_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if token is None:
        pytest.skip("GITHUB_TOKEN not set")
    return token


@pytest.fixture(scope="session")
def my_vcr() -> vcr.VCR:
    return vcr.VCR(
        cassette_library_dir="tests/integration/cassettes",
        record_mode=RecordMode.ONCE,
        filter_headers=["authorization"],
        filter_query_parameters=["access_token"],
    )

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as backend


@pytest.fixture(autouse=True)
def isolated_activities(monkeypatch):
    monkeypatch.setattr(backend, "activities", deepcopy(backend.activities))
    return backend.activities


@pytest.fixture
def client(isolated_activities):
    with TestClient(backend.app) as test_client:
        yield test_client
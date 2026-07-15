from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(event_log_path=tmp_path / "events.jsonl", seed_demo=True)
    with TestClient(create_app(settings)) as test_client:
        yield test_client

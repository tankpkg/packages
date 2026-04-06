import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from interactions.cli_runner import FlightCliRunner

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture
def runner() -> FlightCliRunner:
    return FlightCliRunner(SCRIPTS_DIR)


@pytest.fixture
def cli_context():
    return {}


def has_serpapi_key() -> bool:
    return bool(os.environ.get("SERPAPI_KEY"))


def has_amadeus_keys() -> bool:
    return bool(
        os.environ.get("AMADEUS_CLIENT_ID") and os.environ.get("AMADEUS_CLIENT_SECRET")
    )


def has_travelpayouts_token() -> bool:
    return bool(os.environ.get("TRAVELPAYOUTS_TOKEN"))


_SKIP_RULES = {
    "requires_serpapi": (has_serpapi_key, "SERPAPI_KEY not set"),
    "requires_amadeus": (has_amadeus_keys, "AMADEUS_CLIENT_ID/SECRET not set"),
    "requires_travelpayouts": (has_travelpayouts_token, "TRAVELPAYOUTS_TOKEN not set"),
}


def pytest_collection_modifyitems(config, items):
    for item in items:
        for tag, (check_fn, reason) in _SKIP_RULES.items():
            if tag in item.keywords and not check_fn():
                item.add_marker(pytest.mark.skip(reason=reason))

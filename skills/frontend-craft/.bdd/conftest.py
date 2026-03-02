# pyright: ignore

# pyright: ignore

import shutil
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from interactions.cli_runner import CliRunner
from support.fixtures import build_fixture_cache_data

SCRIPT_SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "search-components.py"


@pytest.fixture
def cli_runner(tmp_path: Path) -> CliRunner:
    work_dir = tmp_path / "cli"
    work_dir.mkdir(parents=True, exist_ok=True)
    script_dest = work_dir / "search-components.py"
    _ = shutil.copy(SCRIPT_SOURCE, script_dest)
    return CliRunner(script_dest, work_dir, env={"SHADCN_REGISTRY_LIMIT": "0"})


@pytest.fixture
def cache_data():
    return build_fixture_cache_data()


@pytest.fixture
def cli_context():
    return {}


@pytest.fixture
def fresh_cache(cli_runner: CliRunner, cache_data) -> None:
    cli_runner.write_cache(cache_data, mtime=time.time())

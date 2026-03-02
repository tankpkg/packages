# pyright: ignore

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys


@dataclass
class CliResult:
    cmd: list[str]
    stdout: str
    stderr: str
    returncode: int


class CliRunner:
    def __init__(
        self, script_path: Path, work_dir: Path, env: dict | None = None
    ) -> None:
        self.script_path = script_path
        self.work_dir = work_dir
        self.env = env

    @property
    def cache_dir(self) -> Path:
        return self.script_path.parent / ".cache"

    @property
    def cache_file(self) -> Path:
        return self.cache_dir / "all-registries-components.json"

    def write_cache(self, data, mtime: float | None = None) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)
        if mtime is not None:
            os.utime(self.cache_file, (mtime, mtime))

    def remove_cache(self) -> None:
        if self.cache_file.exists():
            self.cache_file.unlink()
        if self.cache_dir.exists() and not any(self.cache_dir.iterdir()):
            self.cache_dir.rmdir()

    def run(self, args: list[str]) -> CliResult:
        cmd = [sys.executable, str(self.script_path), *args]
        env = os.environ.copy()
        if self.env:
            env.update(self.env)
        completed = subprocess.run(
            cmd,
            cwd=self.work_dir,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        return CliResult(
            cmd=cmd,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )

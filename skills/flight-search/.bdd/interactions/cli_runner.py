from dataclasses import dataclass
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


class FlightCliRunner:
    def __init__(self, scripts_dir: Path, env_overrides: dict | None = None) -> None:
        self.scripts_dir = scripts_dir
        self.env_overrides = env_overrides or {}

    def _build_env(self, strip_keys: list[str] | None = None) -> dict:
        env = os.environ.copy()
        env.update(self.env_overrides)
        for key in strip_keys or []:
            env.pop(key, None)
        return env

    def run_script(
        self,
        script_name: str,
        args: list[str],
        strip_env_keys: list[str] | None = None,
    ) -> CliResult:
        script = self.scripts_dir / script_name
        cmd = [sys.executable, str(script), *args]
        env = self._build_env(strip_keys=strip_env_keys)
        completed = subprocess.run(
            cmd, text=True, capture_output=True, check=False, env=env
        )
        return CliResult(
            cmd=cmd,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )

    def airport_lookup(self, query: str, json_output: bool = False) -> CliResult:
        args = [query]
        if json_output:
            args.append("--json")
        return self.run_script("airport_lookup.py", args)

    def search_flights(
        self, args: list[str], strip_api_keys: bool = False
    ) -> CliResult:
        strip = (
            ["SERPAPI_KEY", "AMADEUS_CLIENT_ID", "AMADEUS_CLIENT_SECRET"]
            if strip_api_keys
            else None
        )
        return self.run_script("search_flights.py", args, strip_env_keys=strip)

    def price_calendar(
        self, args: list[str], strip_api_keys: bool = False
    ) -> CliResult:
        strip = ["TRAVELPAYOUTS_TOKEN"] if strip_api_keys else None
        return self.run_script("price_calendar.py", args, strip_env_keys=strip)

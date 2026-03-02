# pyright: ignore

import json
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pytest_bdd import given, parsers, scenarios, then, when  # type: ignore

from interactions.cli_runner import CliRunner


scenarios("../features/cache_behavior.feature")
scenarios("../features/search.feature")
scenarios("../features/json_output.feature")
scenarios("../features/install.feature")
scenarios("../features/sources_and_help.feature")


def _parse_total(stdout: str) -> int:
    match = re.search(r"Total:\s+(\d+)\s+cached matches", stdout)
    if not match:
        raise AssertionError("Total line not found in output")
    return int(match.group(1))


@given("no cache file exists")
def given_no_cache(cli_runner: CliRunner) -> None:
    cli_runner.remove_cache()


@given("a fresh cache")
def given_fresh_cache(fresh_cache) -> None:
    _ = fresh_cache
    return None


@given(parsers.parse("a stale cache older than {hours:d} hours"))
def given_stale_cache(
    cli_runner: CliRunner,
    cache_data: Dict[str, Any],
    cli_context: Dict[str, Any],
    hours: int,
) -> None:
    mtime = time.time() - (hours * 3600 + 5)
    cli_runner.write_cache(cache_data, mtime=mtime)
    cli_context["stale_mtime"] = mtime


@when(parsers.parse('I run a search for "{query}"'))
def when_run_search(
    cli_runner: CliRunner, cli_context: Dict[str, Any], query: str
) -> None:
    cli_context["result"] = cli_runner.run([query])
    cli_context["last_query"] = query


@when(parsers.parse('I run a JSON search for "{query}"'))
def when_run_json_search(
    cli_runner: CliRunner, cli_context: Dict[str, Any], query: str
) -> None:
    cli_context["result"] = cli_runner.run([query, "--json"])
    cli_context["last_query"] = query


@when(parsers.parse('I run the CLI with arguments "{args}"'))
def when_run_cli_args(
    cli_runner: CliRunner, cli_context: Dict[str, Any], args: str
) -> None:
    arg_list = [] if args.strip() == "" else shlex.split(args)
    cli_context["result"] = cli_runner.run(arg_list)


@when(parsers.parse('I run a search for "{query}" and store total as "{key}"'))
def when_run_search_store_total(
    cli_runner: CliRunner, cli_context: Dict[str, Any], query: str, key: str
) -> None:
    result = cli_runner.run([query])
    cli_context["result"] = result
    cli_context.setdefault("totals", {})[key] = _parse_total(result.stdout)


@then(parsers.parse('stdout contains "{text}"'))
def then_stdout_contains(cli_context: Dict[str, Any], text: str) -> None:
    assert text in cli_context["result"].stdout


@then(parsers.parse('stdout does not contain "{text}"'))
def then_stdout_not_contains(cli_context: Dict[str, Any], text: str) -> None:
    assert text not in cli_context["result"].stdout


@then(parsers.parse('stderr contains "{text}"'))
def then_stderr_contains(cli_context: Dict[str, Any], text: str) -> None:
    assert text in cli_context["result"].stderr


@then(parsers.parse("the exit code is {code:d}"))
def then_exit_code(cli_context: Dict[str, Any], code: int) -> None:
    assert cli_context["result"].returncode == code


@then("the cache file exists")
def then_cache_file_exists(cli_runner: CliRunner) -> None:
    assert cli_runner.cache_file.exists()


@then("JSON output is a list")
def then_json_is_list(cli_context: Dict[str, Any]) -> None:
    data = json.loads(cli_context["result"].stdout or "[]")
    assert isinstance(data, list)
    cli_context["json_data"] = data


@then("JSON output is an empty list")
def then_json_is_empty(cli_context: Dict[str, Any]) -> None:
    data = json.loads(cli_context["result"].stdout or "[]")
    assert data == []
    cli_context["json_data"] = data


@then(parsers.parse('every JSON item includes fields "{fields}"'))
def then_json_fields_present(cli_context: Dict[str, Any], fields: str) -> None:
    required = [f.strip() for f in fields.split(",") if f.strip()]
    data = cli_context.get("json_data")
    assert isinstance(data, list)
    for item in data:
        for field in required:
            assert field in item


@when("I run the CLI with no arguments")
def when_run_cli_no_args(cli_runner: CliRunner, cli_context) -> None:
    cli_context["result"] = cli_runner.run([])


@then(parsers.parse('totals "{left}" and "{right}" are equal'))
def then_totals_equal(cli_context: Dict[str, Any], left: str, right: str) -> None:
    totals = cli_context.get("totals", {})
    assert totals.get(left) == totals.get(right)

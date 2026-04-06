import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import shlex

from pytest_bdd import given, parsers, scenarios, then, when

from interactions.cli_runner import FlightCliRunner

scenarios("../features/airport_lookup.feature")
scenarios("../features/search_flights.feature")
scenarios("../features/price_calendar.feature")


@when(parsers.parse('I look up airport "{query}"'))
def when_lookup_airport(
    runner: FlightCliRunner, cli_context: dict[str, Any], query: str
) -> None:
    cli_context["result"] = runner.airport_lookup(query)


@when(parsers.parse('I look up airport "{query}" with JSON output'))
def when_lookup_airport_json(
    runner: FlightCliRunner, cli_context: dict[str, Any], query: str
) -> None:
    cli_context["result"] = runner.airport_lookup(query, json_output=True)


@when(parsers.parse('I search flights without API keys using "{args}"'))
def when_search_no_keys(
    runner: FlightCliRunner, cli_context: dict[str, Any], args: str
) -> None:
    cli_context["result"] = runner.search_flights(
        shlex.split(args), strip_api_keys=True
    )


@when(parsers.parse('I search flights with "{args}"'))
def when_search_flights(
    runner: FlightCliRunner, cli_context: dict[str, Any], args: str
) -> None:
    cli_context["result"] = runner.search_flights(shlex.split(args))


@when(parsers.parse('I search flights without serpapi using "{args}"'))
def when_search_no_serpapi(
    runner: FlightCliRunner, cli_context: dict[str, Any], args: str
) -> None:
    cli_context["result"] = runner.run_script(
        "search_flights.py", shlex.split(args), strip_env_keys=["SERPAPI_KEY"]
    )


@when(parsers.parse('I run search_flights with "{args}"'))
def when_run_search_raw(
    runner: FlightCliRunner, cli_context: dict[str, Any], args: str
) -> None:
    cli_context["result"] = runner.search_flights(shlex.split(args))


@when(parsers.parse('I run price_calendar without API keys using "{args}"'))
def when_price_cal_no_keys(
    runner: FlightCliRunner, cli_context: dict[str, Any], args: str
) -> None:
    cli_context["result"] = runner.price_calendar(
        shlex.split(args), strip_api_keys=True
    )


@when(parsers.parse('I run price_calendar with "{args}"'))
def when_run_price_cal(
    runner: FlightCliRunner, cli_context: dict[str, Any], args: str
) -> None:
    cli_context["result"] = runner.price_calendar(shlex.split(args))


@then(parsers.parse('stdout contains "{text}"'))
def then_stdout_contains(cli_context: dict[str, Any], text: str) -> None:
    assert text in cli_context["result"].stdout, (
        f"Expected '{text}' in stdout.\nActual stdout:\n{cli_context['result'].stdout}"
    )


@then(parsers.parse('stderr contains "{text}"'))
def then_stderr_contains(cli_context: dict[str, Any], text: str) -> None:
    assert text in cli_context["result"].stderr, (
        f"Expected '{text}' in stderr.\nActual stderr:\n{cli_context['result'].stderr}"
    )


@then(parsers.parse("the exit code is {code:d}"))
def then_exit_code(cli_context: dict[str, Any], code: int) -> None:
    assert cli_context["result"].returncode == code, (
        f"Expected exit code {code}, got {cli_context['result'].returncode}.\n"
        f"stdout: {cli_context['result'].stdout[:500]}\n"
        f"stderr: {cli_context['result'].stderr[:500]}"
    )


@then("the exit code is not 0")
def then_exit_code_nonzero(cli_context: dict[str, Any]) -> None:
    assert cli_context["result"].returncode != 0


@then(parsers.parse('JSON output contains key "{key}"'))
def then_json_has_key(cli_context: dict[str, Any], key: str) -> None:
    data = json.loads(cli_context["result"].stdout)
    cli_context["json_data"] = data
    assert key in data, f"Key '{key}' not in JSON output. Keys: {list(data.keys())}"


@then("JSON results list is not empty")
def then_json_results_not_empty(cli_context: dict[str, Any]) -> None:
    data = json.loads(cli_context["result"].stdout)
    assert len(data.get("results", [])) > 0, "Expected non-empty results list"


@then("JSON results list is empty")
def then_json_results_empty(cli_context: dict[str, Any]) -> None:
    data = json.loads(cli_context["result"].stdout)
    assert len(data.get("results", [])) == 0, (
        f"Expected empty results, got {len(data.get('results', []))}"
    )


@then("JSON flights list is not empty")
def then_json_flights_not_empty(cli_context: dict[str, Any]) -> None:
    data = json.loads(cli_context["result"].stdout)
    assert len(data.get("flights", [])) > 0, "Expected non-empty flights list"


@then("JSON calendar list is not empty")
def then_json_calendar_not_empty(cli_context: dict[str, Any]) -> None:
    data = json.loads(cli_context["result"].stdout)
    assert len(data.get("calendar", [])) > 0, "Expected non-empty calendar list"


@then(parsers.parse('each flight has "{field}"'))
def then_each_flight_has_field(cli_context: dict[str, Any], field: str) -> None:
    data = json.loads(cli_context["result"].stdout)
    for i, flight in enumerate(data.get("flights", [])):
        assert field in flight, (
            f"Flight #{i} missing field '{field}'. Keys: {list(flight.keys())}"
        )


@then(parsers.parse("every flight has {stops:d} stops"))
def then_every_flight_stops(cli_context: dict[str, Any], stops: int) -> None:
    data = json.loads(cli_context["result"].stdout)
    for i, flight in enumerate(data.get("flights", [])):
        assert flight.get("stops") == stops, (
            f"Flight #{i} has {flight.get('stops')} stops, expected {stops}"
        )

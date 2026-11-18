"""Run small, offline scenarios from the showcase fixture."""

import argparse
from copy import deepcopy
import json
from pathlib import Path


DEFAULT_FIXTURE = Path(__file__).resolve().parents[1] / "configs" / "scenarios.json"


def require_fields(record, **fields):
    if type(record) is not dict:
        raise ValueError("Expected a JSON object")
    for name, expected_type in fields.items():
        value = record.get(name)
        if type(value) is not expected_type:
            raise ValueError(f"Expected {name!r} to be {expected_type.__name__}")


def review_assignments(config):
    require_fields(config, allowed_workspace=str, allowed_task=str, requests=list)
    outcomes = []
    for request in config["requests"]:
        require_fields(request, workspace=str, task=str, checks_passed=bool)
        in_scope = (
            request["workspace"] == config["allowed_workspace"]
            and request["task"] == config["allowed_task"]
        )
        if not in_scope:
            outcomes.append("denied_scope")
        elif request["checks_passed"]:
            outcomes.append("ready_for_review")
        else:
            outcomes.append("needs_follow_up")
    return outcomes


def evaluate_models(config):
    require_fields(config, allowed_provider=str, runs=list)
    outcomes = []
    for run in config["runs"]:
        require_fields(run, provider=str, latency_ms=int, checks_passed=bool)
        if run["latency_ms"] < 0:
            raise ValueError("Latency cannot be negative")
        if run["provider"] != config["allowed_provider"]:
            outcomes.append("provider_denied")
        elif run["checks_passed"]:
            outcomes.append("eligible")
        else:
            outcomes.append("checks_failed")
    return outcomes


def evaluate_desktop_actions(config):
    require_fields(config, requests=list)
    outcomes = []
    for request in config["requests"]:
        require_fields(
            request, action=str, accessible_matches=int,
            clickable_point=bool, screenshot_estimate=bool,
        )
        action = request["action"]
        matches = request["accessible_matches"]
        if action not in ("click", "point"):
            raise ValueError("Desktop action must be click or point")
        if matches < 0:
            raise ValueError("Accessible match count cannot be negative")
        if matches > 1:
            outcome = "ambiguous_target"
        elif action == "click":
            outcome = (
                "click_allowed"
                if matches == 1 and request["clickable_point"]
                else "click_denied_unverified"
            )
        elif matches == 1:
            outcome = "point_accessible"
        elif request["screenshot_estimate"]:
            outcome = "point_estimate"
        else:
            outcome = "target_not_found"
        outcomes.append(outcome)
    return outcomes


def replay_voice_events(config):
    require_fields(config, events=list)
    active_request = None
    latest_request = 0
    outcomes = []
    for event in config["events"]:
        require_fields(event, action=str, request=int)
        request = event["request"]
        if request <= 0:
            raise ValueError("Voice request ID must be positive")
        if event["action"] == "listen":
            require_fields(event, permission=bool)
        match event["action"]:
            case "listen" if request <= latest_request:
                outcomes.append("ignored")
            case "listen":
                latest_request = request
                active_request = request if event["permission"] else None
                outcomes.append("listening" if active_request is not None else "permission_denied")
            case "cancel" if request == active_request:
                active_request = None
                outcomes.append("canceled")
            case "complete" if request == active_request:
                active_request = None
                outcomes.append("response_ready")
            case "cancel" | "complete":
                outcomes.append("ignored")
            case _:
                raise ValueError("Voice action must be listen, cancel, or complete")
    return outcomes


def _buy(save, offer, item, price):
    if offer in save["receipts"]:
        return "sold_out"
    if save["coins"] < price:
        return "insufficient_funds"
    save["coins"] -= price
    save["items"].append(item)
    save["receipts"].append(offer)
    return "purchased"


def replay_purchase(config):
    require_fields(config, offer=str, item=str, price=int, initial_save=dict)
    save = deepcopy(config["initial_save"])
    require_fields(save, coins=int, items=list, receipts=list)
    if not config["offer"].strip() or not config["item"].strip():
        raise ValueError("Offer and item IDs must not be empty")
    if config["price"] <= 0 or save["coins"] < 0:
        raise ValueError("Expected a positive price and a nonnegative balance")
    if any(type(item) is not str or not item.strip() for item in save["items"]):
        raise ValueError("Saved item IDs must be nonempty strings")
    receipts = save["receipts"]
    if any(type(receipt) is not str or not receipt.strip() for receipt in receipts):
        raise ValueError("Saved receipt IDs must be nonempty strings")
    if len(set(receipts)) != len(receipts):
        raise ValueError("Saved receipts must be unique")
    offer = config["offer"], config["item"], config["price"]
    first_purchase = _buy(save, *offer)
    restored = json.loads(json.dumps(save))
    after_reload = _buy(restored, *offer)
    return {
        "first_purchase": first_purchase,
        "after_reload": after_reload,
        "save": restored,
    }


def main(argv=None, *, fixture=DEFAULT_FIXTURE):
    scenarios = {
        "workflows": review_assignments,
        "models": evaluate_models,
        "desktop": evaluate_desktop_actions,
        "voice": replay_voice_events,
        "game": replay_purchase,
    }
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=["all", *scenarios])
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)
    names = scenarios if args.scenario == "all" else [args.scenario]

    try:
        config = json.loads(fixture.read_text(encoding="utf-8"))
        require_fields(config, **dict.fromkeys(names, dict))
        results = {}
        for name in names:
            try:
                results[name] = scenarios[name](config[name])
                if args.verify:
                    require_fields(config[name], expected=type(results[name]))
            except ValueError as error:
                raise ValueError(f"{name}: {error}") from error
    except OSError:
        parser.exit(2, "Could not read the demo fixture.\n")
    except ValueError as error:
        parser.exit(2, f"Invalid demo fixture: {error}\n")

    print(json.dumps(results, indent=2))
    if args.verify:
        failures = [name for name, result in results.items() if result != config[name]["expected"]]
        if failures:
            parser.exit(1, f"Fixture comparison failed for {', '.join(failures)}\n")
        print(f"Verified {len(results)} scenario(s).")


if __name__ == "__main__":
    main()

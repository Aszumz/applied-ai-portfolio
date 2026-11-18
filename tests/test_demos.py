"""Regression checks for the offline demo and its input boundary."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest

from demos import run


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(run.DEFAULT_FIXTURE.read_text(encoding="utf-8"))

    def test_public_fixture_expectations(self):
        handlers = {
            "workflows": run.review_assignments,
            "models": run.evaluate_models,
            "desktop": run.evaluate_desktop_actions,
            "voice": run.replay_voice_events,
            "game": run.replay_purchase,
        }
        self.assertEqual(set(handlers), set(self.fixture))
        for name, handler in handlers.items():
            with self.subTest(scenario=name):
                self.assertEqual(handler(self.fixture[name]), self.fixture[name]["expected"])

    def test_workflow_rejects_an_unapproved_task_in_approved_workspace(self):
        config = self.fixture["workflows"]
        config["requests"][0]["task"] = "publish-build"
        self.assertEqual(run.review_assignments(config)[0], "denied_scope")

    def test_workflow_rejects_string_as_validation_evidence(self):
        config = self.fixture["workflows"]
        config["requests"][0]["checks_passed"] = "false"
        with self.assertRaisesRegex(ValueError, "checks_passed"):
            run.review_assignments(config)

    def test_model_missing_validation_is_invalid(self):
        config = self.fixture["models"]
        del config["runs"][0]["checks_passed"]
        with self.assertRaisesRegex(ValueError, "checks_passed"):
            run.evaluate_models(config)

    def test_model_rejects_invalid_latency(self):
        config = self.fixture["models"]
        for latency in (-1, True, "93"):
            with self.subTest(latency=latency):
                config["runs"][0]["latency_ms"] = latency
                with self.assertRaisesRegex(ValueError, "[Ll]atency"):
                    run.evaluate_models(config)

    def test_desktop_click_requires_clickable_point(self):
        config = self.fixture["desktop"]
        config["requests"][-1]["clickable_point"] = False
        self.assertEqual(run.evaluate_desktop_actions(config)[-1], "click_denied_unverified")

    def test_desktop_point_requires_accessibility_or_estimate(self):
        config = self.fixture["desktop"]
        request = config["requests"][0]
        request["screenshot_estimate"] = False
        self.assertEqual(run.evaluate_desktop_actions(config)[0], "target_not_found")
        request["accessible_matches"] = 1
        self.assertEqual(run.evaluate_desktop_actions(config)[0], "point_accessible")

    def test_desktop_rejects_unknown_action_and_negative_matches(self):
        config = self.fixture["desktop"]
        request = config["requests"][0]
        request["action"] = "type"
        with self.assertRaisesRegex(ValueError, "click or point"):
            run.evaluate_desktop_actions(config)
        request.update(action="click", accessible_matches=-1)
        with self.assertRaisesRegex(ValueError, "negative"):
            run.evaluate_desktop_actions(config)

    def test_voice_ignores_duplicate_listen_and_completion(self):
        events = [
            {"action": "listen", "request": 4, "permission": True},
            {"action": "listen", "request": 4, "permission": True},
            {"action": "listen", "request": 1, "permission": True},
            {"action": "cancel", "request": 1},
            {"action": "complete", "request": 4},
            {"action": "complete", "request": 4},
        ]
        self.assertEqual(
            run.replay_voice_events({"events": events}),
            ["listening", "ignored", "ignored", "ignored", "response_ready", "ignored"],
        )

    def test_voice_denial_does_not_accept_late_results(self):
        events = [
            {"action": "listen", "request": 1, "permission": True},
            {"action": "listen", "request": 2, "permission": False},
            {"action": "complete", "request": 1},
            {"action": "complete", "request": 2},
        ]
        self.assertEqual(
            run.replay_voice_events({"events": events}),
            ["listening", "permission_denied", "ignored", "ignored"],
        )

    def test_voice_rejects_malformed_events(self):
        bad_events = [
            {"action": "listen", "request": 1},
            {"action": "listen", "request": 1, "permission": "false"},
            {"action": "listen", "request": True, "permission": True},
            {"action": "cancel", "request": 0},
            {"action": "upload", "request": 1},
        ]
        for event in bad_events:
            with self.subTest(event=event), self.assertRaises(ValueError):
                run.replay_voice_events({"events": [event]})

    def test_game_insufficient_funds_leave_save_unchanged(self):
        config = self.fixture["game"]
        config["initial_save"]["coins"] = 2
        start_state = deepcopy(config["initial_save"])
        outcome = run.replay_purchase(config)
        self.assertEqual(outcome["first_purchase"], "insufficient_funds")
        self.assertEqual(outcome["after_reload"], "insufficient_funds")
        self.assertEqual(outcome["save"], start_state)
        self.assertEqual(config["initial_save"], start_state)

    def test_game_rejects_repeat_offer_with_no_item_in_inventory(self):
        config = self.fixture["game"]
        config["initial_save"]["receipts"] = [config["offer"]]
        config["initial_save"]["items"] = []
        start_state = deepcopy(config["initial_save"])
        outcome = run.replay_purchase(config)
        self.assertEqual(outcome["first_purchase"], "sold_out")
        self.assertEqual(outcome["after_reload"], "sold_out")
        self.assertEqual(outcome["save"], start_state)

    def test_game_success_does_not_mutate_input_save(self):
        config = self.fixture["game"]
        before = deepcopy(config)
        run.replay_purchase(config)
        self.assertEqual(config, before)

    def test_game_rejects_malformed_save(self):
        for field, value in (
            ("coins", -1), ("coins", False), ("items", [3]),
            ("receipts", ["duplicate", "duplicate"]), ("receipts", [" "]),
        ):
            with self.subTest(field=field, value=value):
                config = deepcopy(self.fixture["game"])
                config["initial_save"][field] = value
                with self.assertRaises(ValueError):
                    run.replay_purchase(config)

    def test_game_rejects_non_positive_prices(self):
        config = self.fixture["game"]
        for price in (0, -3):
            with self.subTest(price=price):
                config["price"] = price
                with self.assertRaisesRegex(ValueError, "positive price"):
                    run.replay_purchase(config)

    def run_cli(self, data, *args):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            if data is not None:
                path.write_text(data, encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr), self.assertRaises(SystemExit) as result:
                run.main(args, fixture=path)
        return result.exception.code, stdout.getvalue(), stderr.getvalue()

    def test_cli_rejects_invalid_json_and_non_object_root(self):
        for data in ("{broken", "[]"):
            with self.subTest(data=data):
                status, output, error = self.run_cli(data, "all", "--verify")
                self.assertEqual(status, 2)
                self.assertEqual(output, "")
                self.assertIn("Invalid demo fixture", error)

    def test_cli_rejects_missing_fixture(self):
        status, output, error = self.run_cli(None, "game")
        self.assertEqual((status, output), (2, ""))
        self.assertIn("Could not read", error)

    def test_cli_rejects_missing_expected_result(self):
        del self.fixture["game"]["expected"]
        status, output, error = self.run_cli(json.dumps(self.fixture), "game", "--verify")
        self.assertEqual((status, output), (2, ""))
        self.assertIn("expected", error)

    def test_cli_reports_mismatch_distinct_from_bad_input(self):
        self.fixture["game"]["expected"] = {}
        status, output, error = self.run_cli(json.dumps(self.fixture), "game", "--verify")
        self.assertEqual(status, 1)
        self.assertIn("purchased", output)
        self.assertIn("Fixture comparison failed for game", error)

    def test_cli_unknown_scenario_is_a_usage_error(self):
        status, output, error = self.run_cli("{}", "missing")
        self.assertEqual((status, output), (2, ""))
        self.assertIn("invalid choice", error)


if __name__ == "__main__":
    unittest.main()

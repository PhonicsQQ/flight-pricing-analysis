"""Synthetic unit fixtures only; never collected data or research findings."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from flights.collect import (PILOT_CAP, check_account, collect, locked_store,
                             make_plan, query_id, redact, reserve, validate_plan)
from flights.process import audit, daily_series, exact_changes, normalize, revision_audit


def ts(day):
    return int(datetime.fromisoformat(day + "T12:00:00+00:00").timestamp())


def snapshot(history, sid="s1"):
    p = make_plan(date(2026, 10, 30))["queries"][0]["params"]
    return dict(params=p, search_id=query_id(p), snapshot_id=sid, role="baseline",
                outcome="success", retrieved_at="2026-11-05T23:00:00+00:00",
                response={"price_insights": {"price_history": history}})


class ProcessingTests(unittest.TestCase):
    def test_timezone_lead_and_dst(self):
        # 02:00 UTC on Nov 2 is still Nov 1 in Baltimore after DST ends.
        stamp = datetime(2026, 11, 2, 2, tzinfo=timezone.utc).timestamp()
        rows, _ = normalize(snapshot([[stamp, 100]]))
        self.assertEqual(rows[0]["observation_date"], "2026-11-01")
        self.assertEqual(rows[0]["observation_date_utc"], "2026-11-02")
        self.assertEqual(rows[0]["days_until_departure"], 5)
        self.assertEqual(rows[0]["observation_weekday"], "Sunday")
        self.assertEqual(rows[0]["departure_weekday"], "Friday")

    def test_exact_horizon_not_next_available(self):
        rows, _ = normalize(snapshot([[ts("2026-10-28"), 100], [ts("2026-11-01"), 120], [ts("2026-11-04"), 90]]))
        self.assertEqual(exact_changes(rows, 1), [])
        pairs = exact_changes(rows, 7)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["change_usd"], -10)
        self.assertEqual(pairs[0]["change_percent"], -10)
        self.assertEqual(len(exact_changes(rows, 3)), 1)

    def test_duplicates_conflicts_and_daily_ambiguity(self):
        rows, _ = normalize(snapshot([[ts("2026-11-01"), 100]] * 2))
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(daily_series(rows)), 1)
        rows, _ = normalize(snapshot([[ts("2026-11-01"), 100], [ts("2026-11-01"), 110]]))
        self.assertEqual(daily_series(rows), [])
        rows, _ = normalize(snapshot([[ts("2026-11-01"), 100], [ts("2026-11-01") + 3600, 110]]))
        self.assertEqual(daily_series(rows), [])

    def test_missing_and_failed_not_zero(self):
        s = snapshot(None)
        rows, issues = normalize(s)
        self.assertEqual(rows, [])
        self.assertEqual(issues, ["missing_history"])
        s["outcome"] = "failed_or_unknown"
        self.assertEqual(normalize(s)[1], ["request_failed_or_unknown"])

    def test_invalid_prices_and_future_times(self):
        rows, _ = normalize(snapshot([[ts("2026-11-01"), 0], [ts("2026-11-02"), -5],
                                       [ts("2026-11-03"), None], [ts("2026-11-04"), True],
                                       [ts("2026-11-08"), 100]]))
        self.assertFalse(any(r["eligible"] for r in rows))
        self.assertEqual(daily_series(rows), [])

    def test_currency_mismatch_quarantined(self):
        s = snapshot([[ts("2026-11-01"), 100]])
        s["response"]["search_parameters"] = {"currency": "EUR"}
        rows, issues = normalize(s)
        self.assertFalse(rows[0]["eligible"])
        self.assertTrue(issues)

    def test_malformed_nested_schema(self):
        s = snapshot([[ts("2026-11-01"), 100]])
        s["response"]["search_parameters"] = ["unexpected"]
        self.assertEqual(normalize(s), ([], ["invalid_search_parameters_schema"]))

    def test_snapshot_revision_and_no_cross_snapshot_pairs(self):
        a, _ = normalize(snapshot([[ts("2026-10-28"), 100]]))
        b, _ = normalize(snapshot([[ts("2026-10-28"), 110], [ts("2026-11-04"), 120]], "s2"))
        self.assertEqual(len(revision_audit(a + b)), 1)
        pairs = exact_changes(a + b, 7)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["change_usd"], 10)

    def test_empty_audit_has_no_findings(self):
        with TemporaryDirectory() as temp:
            result = audit(Path(temp))
            self.assertEqual(result["status"], "NO_DATA")
            self.assertEqual(result["baseline_independent_trip_count"], 0)

    def test_audit_retains_raw_snapshots_deduplicates_latest(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "raw").mkdir()
            for sid, price in (("s1", 100), ("s2", 110)):
                s = snapshot([[ts("2026-10-28"), price], [ts("2026-11-04"), 120]], sid)
                (root / "raw" / f"{sid}.json").write_text(json.dumps(s))
            result = audit(root)
            self.assertEqual(result["snapshot_count"], 2)
            self.assertEqual(result["baseline_independent_trip_count"], 1)
            self.assertEqual(result["usable_baseline_daily_observations"], 2)
            self.assertEqual(len(result["revisions"]), 1)


class CollectorTests(unittest.TestCase):
    def test_plan_eight_queries_six_trips(self):
        p = make_plan(date(2026, 10, 30))
        validate_plan(p)
        self.assertEqual(len(p["queries"]), 8)
        self.assertEqual(sum(q["role"] == "baseline" for q in p["queries"]), 6)
        p["queries"][0]["params"]["api_key"] = "not-allowed"
        with self.assertRaises(ValueError):
            validate_plan(p)

    def test_diagnostic_modes_keep_fare_constraints(self):
        p = make_plan(date(2026, 10, 30))
        p['queries'][0]['params'].update(sort_by=1, deep_search='false')
        validate_plan(p)
        p['queries'][0]['params']['travel_class'] = 3
        with self.assertRaises(ValueError):
            validate_plan(p)

    def test_lifetime_cap_survives_restart(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with locked_store(root) as c:
                for _ in range(PILOT_CAP):
                    reserve(c, {})
            with locked_store(root) as c:
                with self.assertRaises(RuntimeError):
                    reserve(c, {})
                self.assertEqual(c.execute("SELECT COUNT(*) FROM attempts").fetchone()[0], PILOT_CAP)

    def test_authorized_extension_manifests(self):
        for role in ('diagnostic_minimal', 'diagnostic_fresh', 'diagnostic_roundtrip'):
            plan = json.loads((Path('config') / (role + '.json')).read_text())
            validate_plan(plan)
            self.assertNotEqual(plan['queries'][0]['role'], 'baseline')
            plan['queries'][0]['params']['api_key'] = 'forbidden-fixture'
            with self.assertRaises(ValueError):
                validate_plan(plan)

    def test_concurrent_run_refused(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            def second():
                with locked_store(root):
                    return "unexpected"
            with locked_store(root), ThreadPoolExecutor(1) as pool:
                with self.assertRaises(RuntimeError):
                    pool.submit(second).result()

    def test_account_rejects_paid_missing_and_exhausted(self):
        for payload in ({}, {"plan_monthly_price": 25, "plan_name": "Starter"},
                        {"plan_monthly_price": 0, "plan_name": "Free", "plan_searches_left": 0}):
            with self.assertRaises(RuntimeError):
                check_account("fixture", lambda *args: (200, payload))

    def test_protected_quota_floor(self):
        payload = dict(plan_name='Free Plan', plan_monthly_price=0,
                       plan_searches_left=40, account_rate_limit_per_hour=250, this_hour_searches=0)
        with self.assertRaises(RuntimeError):
            check_account('fixture', lambda *args: (200,payload))

    def test_study_manifest_preserves_constraints(self):
        p = json.loads(Path('config/study.json').read_text())
        validate_plan(p)
        self.assertEqual(len(p['queries']),168)
        p['queries'][0]['params']['stops'] = 0
        with self.assertRaises(ValueError):
            validate_plan(p)

    def test_redaction_in_nested_urls(self):
        x = redact({"api_key": "abc", "nested": ["https://example.test/?api_key=abc"]}, "abc")
        self.assertNotIn("abc", json.dumps(x))

    def test_mock_collection_cache_budget_and_raw(self):
        calls = []
        def fake(endpoint, params, key):
            calls.append(endpoint)
            if endpoint == "account.json":
                return 200, dict(plan_name="Free", plan_monthly_price=0, plan_searches_left=250,
                                 account_rate_limit_per_hour=50, this_hour_searches=0)
            return 200, {"search_metadata": {"status": "Success"}, "api_key": key}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            plan = make_plan(date(2099, 1, 1))
            self.assertEqual(collect(plan, "fixture-secret", root=root, transport=fake), 8)
            self.assertEqual(collect(plan, "fixture-secret", root=root, transport=fake), 0)
            self.assertEqual(calls.count("search.json"), 8)
            self.assertEqual(len(list((root / "raw").glob("*.json"))), 8)
            self.assertNotIn("fixture-secret", "".join(p.read_text() for p in (root / "raw").glob("*.json")))

    def test_retry_is_bounded_and_budgeted(self):
        calls = []
        def fake(endpoint, params, key):
            if endpoint == "account.json":
                return 200, dict(plan_name="Free", plan_monthly_price=0, plan_searches_left=250,
                                 account_rate_limit_per_hour=50, this_hour_searches=0)
            calls.append(endpoint)
            return 503, {"error": "fixture"}
        with TemporaryDirectory() as temp:
            with self.assertRaises(RuntimeError):
                collect(make_plan(date(2099, 1, 1)), "fixture", root=Path(temp), transport=fake, sleep=lambda _: None)
            with locked_store(Path(temp)) as c:
                self.assertEqual(c.execute("SELECT COUNT(*) FROM attempts").fetchone()[0], 2)
            self.assertEqual(len(calls), 2)

    def test_unknown_provider_status_preserved_as_failure(self):
        def fake(endpoint, params, key):
            if endpoint == "account.json":
                return 200, dict(plan_name="Free", plan_monthly_price=0, plan_searches_left=250,
                                 account_rate_limit_per_hour=50, this_hour_searches=0)
            return 200, {"search_metadata": None}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(RuntimeError):
                collect(make_plan(date(2099, 1, 1)), "fixture", root=root, transport=fake)
            saved = json.loads(next((root / "raw").glob("*.json")).read_text())
            self.assertEqual(saved["outcome"], "failed_or_unknown")
            self.assertIsNone(saved["response"]["search_metadata"])

    def test_dry_run_without_credentials(self):
        result = subprocess.run([sys.executable, "-m", "flights.collect", "run"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no network calls", result.stdout)


if __name__ == "__main__":
    unittest.main()

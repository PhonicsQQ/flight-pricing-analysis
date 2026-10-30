"""Standard-library collector. Live requests require --live; lifetime collection cap = 200."""
import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import ssl
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import urlopen
import uuid
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PILOT_CAP = 200  # User authorized collection within free quota; reserve provider capacity.
QUOTA_RESERVE = 40


def now():
    return datetime.now(timezone.utc).isoformat()


def query_id(params):
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:20]


def make_plan(anchor):
    base = dict(engine="google_flights", departure_id="BWI", type=2,
                adults=1, children=0, infants_in_seat=0, infants_on_lap=0,
                travel_class=1, stops=1, currency="USD", hl="en", gl="us",
                exclude_basic="false", bags=0, deep_search="true", sort_by=2)
    queries = []
    for destination in ("ATL", "MCO", "DEN"):
        for lead in (7, 32):
            params = dict(base, arrival_id=destination,
                          outbound_date=(anchor + timedelta(days=lead)).isoformat())
            queries.append(dict(role="baseline", params=params))
    for field, value in (("stops", 0), ("exclude_basic", "true")):
        queries.append(dict(role=f"contrast_{field}",
                            params=dict(queries[0]["params"], **{field: value})))
    return dict(schema_version=1, anchor_date=anchor.isoformat(),
                purpose="coverage probes; destinations not yet validated", queries=queries)


def validate_plan(plan):
    if plan.get("schema_version") == 2:
        if not 1 <= len(plan.get("queries", [])) <= 180:
            raise ValueError("Invalid study manifest size")
        ids = []
        for item in plan['queries']:
            p = item['params']
            fixed = dict(engine='google_flights', departure_id='BWI', type=2, adults=1,
                         travel_class=1, currency='USD', hl='en', gl='us')
            required = set(fixed) | {'arrival_id', 'outbound_date', 'stops'}
            if not required <= set(p) or set(p) - required - {'exclude_basic', 'bags'}:
                raise ValueError('Unexpected study parameters')
            if any(p[k] != v for k,v in fixed.items()):
                raise ValueError('Study fare constraints changed')
            if p['arrival_id'] not in ('ATL','MCO','DEN') or p['stops'] not in (0,1):
                raise ValueError('Unapproved route or stop setting')
            if 'exclude_basic' in p and p['exclude_basic'] != 'true':
                raise ValueError('Invalid basic-fare contrast')
            if 'bags' in p and p['bags'] != 0:
                raise ValueError('Invalid bags diagnostic')
            if item['role'] == 'baseline' and (p['stops'] != 1 or set(p) != required):
                raise ValueError('Baseline must use minimal nonstop query')
            if item['role'] not in ('baseline','contrast_stops','contrast_exclude_basic','diagnostic_bags'):
                raise ValueError('Unexpected role')
            date.fromisoformat(p['outbound_date'])
            ids.append(query_id(p))
        if len(ids) != len(set(ids)):
            raise ValueError('Duplicate query')
        return
    if plan.get("schema_version") != 1 or not 1 <= len(plan["queries"]) <= 8:
        raise ValueError("Expected a version-1 pilot manifest with 1–8 queries")
    allowed = set(make_plan(date(2026, 10, 30))["queries"][0]["params"])
    for item in plan["queries"]:
        p = item["params"]
        if item.get("role") in {"diagnostic_minimal", "diagnostic_fresh", "diagnostic_roundtrip"}:
            expected = dict(engine="google_flights", departure_id="BWI", arrival_id="ATL",
                            outbound_date="2026-11-06", type=2, adults=1, travel_class=1,
                            stops=1, currency="USD", hl="en", gl="us")
            if item["role"] == "diagnostic_fresh":
                expected["no_cache"] = "true"
            if item["role"] == "diagnostic_roundtrip":
                expected.update(type=1, return_date="2026-11-13")
            if p != expected:
                raise ValueError("Extended diagnostics must match the three authorized queries")
            continue
        if set(p) != allowed:
            raise ValueError("Unexpected or missing parameters; credentials must never enter manifests")
        fixed = make_plan(date(2026, 10, 30))["queries"][0]["params"]
        varying = {"arrival_id", "outbound_date", "stops", "exclude_basic", "sort_by", "deep_search"}
        if any(p[k] != fixed[k] for k in allowed - varying):
            raise ValueError("Pilot requires fixed BWI, one-way, one-adult economy USD settings")
        if p["stops"] not in (0, 1) or p["exclude_basic"] not in ("true", "false"):
            raise ValueError("Unsupported contrast")
        if p["sort_by"] not in (1, 2) or p["deep_search"] not in ("true", "false"):
            raise ValueError("Unsupported diagnostic search mode")
        if len(p["arrival_id"]) != 3 or not p["arrival_id"].isupper() or not p["arrival_id"].isalpha():
            raise ValueError("Use a single destination airport")
        date.fromisoformat(p["outbound_date"])
    ids = [query_id(x["params"]) for x in plan["queries"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate manifest query")


def load_env():
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                if key.strip() in {"SERPAPI_API_KEY", "SERPAPI_FREE_PLAN_CONFIRMED"}:
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def redact(value, secret):
    """Sanitize full response, including embedded URLs; never persist account payloads."""
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if k.lower() in {"api_key", "authorization"}
                    else redact(v, secret)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, secret) for v in value]
    if isinstance(value, str) and secret:
        return value.replace(secret, "[REDACTED]").replace(quote(secret, safe=""), "[REDACTED]")
    return value


def request(endpoint, params, key):
    # Never log URL/exception strings: they can contain the key.
    url = "https://serpapi.com/" + endpoint + "?" + urlencode(dict(params, api_key=key))
    try:
        # python.org macOS builds may lack their bundled CA file. Use the
        # system trust bundle, never an unverified TLS context.
        paths = ssl.get_default_verify_paths()
        cafile = None
        if (sys.platform == "darwin" and not paths.cafile
                and not os.environ.get("SSL_CERT_FILE")
                and Path("/etc/ssl/cert.pem").exists()):
            cafile = "/etc/ssl/cert.pem"
        context = ssl.create_default_context(cafile=cafile)
        with urlopen(url, timeout=90, context=context) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except (ValueError, UnicodeError):
            body = {"error": "non_json_http_error"}
        return exc.code, body
    except (URLError, TimeoutError, OSError):
        return 0, {"error": "transport_error_outcome_unknown"}
    except (ValueError, UnicodeError):
        return 0, {"error": "non_json_response"}


def check_account(key, transport=request):
    status, account = transport("account.json", {}, key)
    if status != 200 or not isinstance(account, dict) or account.get("error"):
        raise RuntimeError("Account verification failed; no search sent")
    if account.get("plan_monthly_price") != 0 or "free" not in str(account.get("plan_name", "")).lower():
        raise RuntimeError("Cannot verify a zero-cost Free plan; no search sent")
    left = account.get("plan_searches_left")
    if type(left) is not int or left <= QUOTA_RESERVE:
        raise RuntimeError("Free monthly quota unavailable or protected reserve reached; no search sent")
    hourly = account.get("account_rate_limit_per_hour")
    used = account.get("this_hour_searches")
    if type(hourly) is not int or type(used) is not int or used >= hourly:
        raise RuntimeError("Hourly capacity unavailable; retry later")
    return {k: account.get(k) for k in ("plan_name", "plan_monthly_price", "plan_searches_left",
                                        "account_rate_limit_per_hour", "this_hour_searches")}


@contextmanager
def locked_store(root=DATA):
    root.mkdir(parents=True, exist_ok=True)
    with (root / "collector.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another collector is running") from None
        conn = sqlite3.connect(root / "ledger.sqlite")
        conn.execute("""CREATE TABLE IF NOT EXISTS attempts (
            snapshot_id TEXT PRIMARY KEY, search_id TEXT, requested_at TEXT,
            params_json TEXT, outcome TEXT, http_status INTEGER, raw_path TEXT)""")
        conn.commit()
        try:
            yield conn
        finally:
            conn.close()
            fcntl.flock(lock, fcntl.LOCK_UN)


def reserve(conn, params):
    # Durable reservation precedes networking. A crash consumes a slot conservatively.
    conn.execute("BEGIN IMMEDIATE")
    if conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] >= PILOT_CAP:
        conn.rollback()
        raise RuntimeError(f"Pilot lifetime request cap ({PILOT_CAP}) reached")
    sid = uuid.uuid4().hex
    conn.execute("INSERT INTO attempts VALUES (?, ?, ?, ?, 'reserved', NULL, NULL)",
                 (sid, query_id(params), now(), json.dumps(params, sort_keys=True)))
    conn.commit()
    return sid


def atomic_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def collect(plan, key, limit=8, refresh=False, retry_failed=False, only=None,
            transport=request, root=DATA, sleep=time.sleep):
    validate_plan(plan)
    if not 1 <= limit <= 180:
        raise ValueError("Run limit must be 1–180")
    if refresh and not only:
        raise ValueError("Refresh requires --only SEARCH_ID to avoid batch refetching")
    sent = 0
    with locked_store(root) as conn:
        for item in plan["queries"]:
            params = item["params"]
            qid = query_id(params)
            if only and only != qid:
                continue
            if date.fromisoformat(params["outbound_date"]) <= datetime.now(ZoneInfo("America/New_York")).date():
                raise ValueError("Manifest contains a departed/today trip; generate and review a new plan")
            previous = conn.execute("SELECT outcome, requested_at FROM attempts WHERE search_id=? ORDER BY requested_at DESC", (qid,)).fetchall()
            if previous and not refresh:
                if any(p[0] == "success" for p in previous) or not retry_failed:
                    print(qid, "cached or previously attempted; skipped")
                    continue
            if previous and refresh and (datetime.now(timezone.utc) - datetime.fromisoformat(previous[0][1])).total_seconds() < 86400:
                raise RuntimeError("Snapshot refresh requires 24 hours between attempts")
            for attempt in range(2):
                if sent >= limit:
                    return sent
                if conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] >= PILOT_CAP:
                    raise RuntimeError(f"Pilot lifetime request cap ({PILOT_CAP}) reached")
                account = check_account(key, transport)
                sid = reserve(conn, params)
                started = now()
                status, payload = transport("search.json", params, key)
                sent += 1
                metadata = payload.get("search_metadata") if isinstance(payload, dict) else None
                success = (status == 200 and isinstance(payload, dict) and not payload.get("error")
                           and isinstance(metadata, dict) and metadata.get("status") == "Success")
                outcome = "success" if success else "failed_or_unknown"
                target = root / "raw" / f"{sid}.json"
                atomic_json(target, dict(schema_version=1, provider="serpapi_google_flights",
                    snapshot_id=sid, search_id=qid, role=item["role"], params=params,
                    requested_at=started, retrieved_at=now(), http_status=status,
                    outcome=outcome, account_quota=account, response=redact(payload, key)))
                conn.execute("UPDATE attempts SET outcome=?, http_status=?, raw_path=? WHERE snapshot_id=?",
                             (outcome, status, str(target.relative_to(root)), sid))
                conn.commit()
                print(qid, outcome, "attempts this run:", sent)
                if success or status not in (429, 500, 502, 503, 504) or attempt == 1:
                    break
                sleep(5)  # One bounded retry, reserved and counted separately.
            if not success:
                raise RuntimeError("Search failed; stopped for inspection (not evidence of no flights)")
    return sent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("account", help="Read and save only non-sensitive quota fields; no flight searches")
    plan = sub.add_parser("plan")
    plan.add_argument("--anchor", default=datetime.now(ZoneInfo("America/New_York")).date().isoformat())
    plan.add_argument("--output", type=Path, default=ROOT / "config/pilot.json")
    run = sub.add_parser("run")
    run.add_argument("--plan", type=Path, default=ROOT / "config/pilot.json")
    run.add_argument("--live", action="store_true")
    run.add_argument("--limit", type=int, default=8)
    run.add_argument("--refresh", action="store_true")
    run.add_argument("--retry-failed", action="store_true")
    run.add_argument("--only")
    args = parser.parse_args()
    if args.command == "account":
        load_env()
        key = os.environ.get('SERPAPI_API_KEY', '')
        if not key:
            raise RuntimeError('Configure credentials locally')
        summary = dict(checked_at=now(), **check_account(key))
        atomic_json(DATA / 'account/latest.json', summary)
        print(json.dumps(summary, indent=2))
        return
    if args.command == "plan":
        if args.output.exists():
            raise ValueError("Manifest exists; use a new output path to preserve the sampling record")
        atomic_json(args.output, make_plan(date.fromisoformat(args.anchor)))
        print("Saved", args.output)
        return
    manifest = json.loads(args.plan.read_text())
    validate_plan(manifest)
    if args.only and args.only not in {query_id(x["params"]) for x in manifest["queries"]}:
        raise ValueError("Unknown --only search ID")
    if not args.live:
        print("DRY RUN: no credentials loaded, no network calls, no quota consumed")
        for q in manifest["queries"]:
            print(query_id(q["params"]), q["role"], json.dumps(q["params"], sort_keys=True))
        print(f"{len(manifest['queries'])} planned queries; lifetime cap {PILOT_CAP} including retries and refreshes")
        return
    load_env()
    key = os.environ.get("SERPAPI_API_KEY", "")
    if not key or os.environ.get("SERPAPI_FREE_PLAN_CONFIRMED", "").lower() != "true":
        raise RuntimeError("Configure the key and Free-plan confirmation in local .env; never share the key in chat")
    collect(manifest, key, args.limit, args.refresh, args.retry_failed, args.only)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from None

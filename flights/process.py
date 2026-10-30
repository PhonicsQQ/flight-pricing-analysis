"""Offline pilot audit; preserves snapshots, flags questionable data, never imputes."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

from flights.collect import DATA, ROOT, atomic_json, query_id

OBSERVATION_ZONE = "America/New_York"  # Provisional convention, not a provider guarantee.


def normalize(snapshot):
    p = snapshot["params"]
    response = snapshot.get("response")
    response = response if isinstance(response, dict) else {}
    insights = response.get("price_insights")
    insights = insights if isinstance(insights, dict) else {}
    history = insights.get("price_history")
    issues = []
    if snapshot.get("outcome") != "success":
        return [], ["request_failed_or_unknown"]
    if history is None:
        return [], ["missing_history"]
    if not isinstance(history, list):
        return [], ["invalid_history_schema"]
    if not history:
        return [], ["empty_history"]
    returned = response.get("search_parameters") or {}
    if not isinstance(returned, dict):
        return [], ["invalid_search_parameters_schema"]
    mismatches = [k for k, v in p.items() if k in returned and str(returned[k]).lower() != str(v).lower()]
    if mismatches:
        issues.append("returned_parameters_differ:" + ",".join(mismatches))
    departure = date.fromisoformat(p["outbound_date"])
    retrieved = datetime.fromisoformat(snapshot["retrieved_at"])
    rows = []
    for index, pair in enumerate(history):
        if not isinstance(pair, list) or len(pair) != 2:
            issues.append(f"invalid_pair:{index}")
            continue
        stamp, price = pair
        if type(stamp) not in (int, float) or not math.isfinite(stamp):
            issues.append(f"invalid_timestamp:{index}")
            continue
        try:
            instant = datetime.fromtimestamp(stamp, timezone.utc)
        except (ValueError, OverflowError, OSError):
            issues.append(f"invalid_timestamp:{index}")
            continue
        observed = instant.astimezone(ZoneInfo(OBSERVATION_ZONE)).date()
        flags = ["historical_filter_semantics_unverified", "timezone_convention_unverified"]
        valid_price = type(price) in (int, float) and math.isfinite(price) and price > 0
        if not valid_price:
            flags.append("invalid_or_nonpositive_price")
        if instant > retrieved:
            flags.append("timestamp_after_retrieval")
        if observed > departure:
            flags.append("observation_after_departure")
        if mismatches:
            flags.append("returned_parameter_mismatch")
        rows.append(dict(search_id=snapshot["search_id"], snapshot_id=snapshot["snapshot_id"],
            retrieved_at=snapshot["retrieved_at"], role=snapshot["role"],
            trip_id=f"{p['departure_id']}-{p['arrival_id']}-{p['outbound_date']}" +
                (f"-roundtrip-{p['return_date']}" if p['type'] == 1 else ""),
            trip_type=p['type'], return_date=p.get('return_date'),
            origin=p["departure_id"], destination=p["arrival_id"], departure_date=p["outbound_date"],
            currency_requested=p["currency"], historical_timestamp=stamp, timestamp_utc=instant.isoformat(),
            observation_date=observed.isoformat(), observation_date_utc=instant.date().isoformat(),
            observation_timezone=OBSERVATION_ZONE, price=price if valid_price else None,
            days_until_departure=(departure - observed).days,
            observation_weekday=observed.strftime("%A"), departure_weekday=departure.strftime("%A"),
            quality_flags=flags, eligible=valid_price and instant <= retrieved and observed <= departure and not mismatches))
    groups = defaultdict(list)
    for row in rows:
        groups[row["historical_timestamp"]].append(row)
    for group in groups.values():
        if len(group) > 1:
            conflicting = len({r["price"] for r in group}) > 1
            for r in group:
                r["quality_flags"].append("conflicting_timestamp" if conflicting else "duplicate_timestamp")
                if conflicting:
                    r["eligible"] = False
    dates = Counter(r["observation_date"] for r in rows)
    for row in rows:
        if dates[row["observation_date"]] > 1:
            row["quality_flags"].append("multiple_rows_on_date")
    return rows, issues


def daily_series(rows):
    """Single snapshot: collapse identical duplicates; omit ambiguous daily values."""
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["observation_date"]].append(row)
    result = []
    for day, group in sorted(grouped.items()):
        if not all(r["eligible"] for r in group) or len({r["price"] for r in group}) != 1:
            continue
        result.append(max(group, key=lambda r: r["historical_timestamp"]))
    return result


def exact_changes(rows, horizon):
    """Exact calendar-date joins; no nearest match, interpolation, or zero filling."""
    if horizon <= 0:
        raise ValueError("Horizon must be positive")
    index = {(r["search_id"], r["snapshot_id"], r["observation_date"]): r for r in rows}
    if len(index) != len(rows):
        raise ValueError("Deduplicate daily series before horizon matching")
    pairs = []
    for row in rows:
        target = (date.fromisoformat(row["observation_date"]) + timedelta(days=horizon)).isoformat()
        end = index.get((row["search_id"], row["snapshot_id"], target))
        if end and row["eligible"] and end["eligible"]:
            delta = end["price"] - row["price"]
            pairs.append(dict(search_id=row["search_id"], trip_id=row["trip_id"],
                snapshot_id=row["snapshot_id"], origin=row["origin"], destination=row["destination"],
                observation_date=row["observation_date"], label_date=target,
                days_until_departure=row["days_until_departure"], horizon_days=horizon,
                price=row["price"], future_price=end["price"], change_usd=delta,
                change_percent=100 * delta / row["price"], direction="up" if delta > 0 else "down" if delta < 0 else "unchanged"))
    return pairs


def revision_audit(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["search_id"], row["historical_timestamp"])].append(row)
    revisions = []
    for (qid, stamp), group in groups.items():
        if len({r["snapshot_id"] for r in group}) > 1 and len({r["price"] for r in group}) > 1:
            revisions.append(dict(search_id=qid, historical_timestamp=stamp,
                                  versions=[{k: r[k] for k in ("snapshot_id", "retrieved_at", "price")} for r in group]))
    return revisions


def audit(root=DATA):
    snapshots = [json.loads(p.read_text()) for p in sorted((root / "raw").glob("*.json"))]
    # Explicit manifest membership can reuse a diagnostic query without changing
    # its original raw provenance. Test stores do not inherit real manifests.
    if root == DATA:
        baseline_ids = set()
        for name in ('validation.json', 'study.json'):
            manifest = ROOT / 'config' / name
            if manifest.exists():
                baseline_ids.update(query_id(q['params']) for q in json.loads(manifest.read_text())['queries']
                                    if q['role'] == 'baseline')
        snapshots = [dict(s, role='baseline') if s['search_id'] in baseline_ids else s for s in snapshots]
    all_rows, summaries, latest, by_snapshot = [], [], {}, {}
    for snap in sorted(snapshots, key=lambda s: (s["retrieved_at"], s["snapshot_id"])):
        rows, issues = normalize(snap)
        all_rows.extend(rows)
        daily = daily_series(rows)
        by_snapshot[snap["snapshot_id"]] = daily
        if snap["outcome"] == "success":
            latest[snap["search_id"]] = snap["snapshot_id"]
        gaps = [(date.fromisoformat(b["observation_date"]) - date.fromisoformat(a["observation_date"])).days
                for a, b in zip(daily, daily[1:])]
        jumps = [dict(start=a["observation_date"], end=b["observation_date"], ratio=b["price"] / a["price"])
                 for a, b in zip(daily, daily[1:]) if b["price"] / a["price"] > 2 or b["price"] / a["price"] < .5]
        minimum = min((r["price"] for r in daily), default=None)
        response = snap.get("response") if isinstance(snap.get("response"), dict) else {}
        insights = response.get("price_insights") or {}
        summaries.append(dict(search_id=snap["search_id"], snapshot_id=snap["snapshot_id"],
            role=snap["role"], params=snap["params"], outcome=snap["outcome"],
            retrieved_at=snap["retrieved_at"], parsed_rows=len(rows), usable_dates=len(daily),
            first_date=daily[0]["observation_date"] if daily else None,
            last_date=daily[-1]["observation_date"] if daily else None,
            last_lead_days=daily[-1]["days_until_departure"] if daily else None,
            missing_calendar_days=sum(g - 1 for g in gaps), issues=issues,
            quality_flag_counts=dict(Counter(f for r in rows for f in r["quality_flags"])),
            large_jumps_for_inspection=jumps, lowest_observed_price=minimum,
            lowest_observed_dates=[r["observation_date"] for r in daily if r["price"] == minimum],
            lowest_observed_lead_days=[r["days_until_departure"] for r in daily if r["price"] == minimum],
            current_price_insights={k: insights.get(k) for k in ("lowest_price", "price_level", "typical_price_range")} if isinstance(insights, dict) else {},
            google_flights_url=(response.get("search_metadata") or {}).get("google_flights_url")
                if isinstance(response.get("search_metadata"), dict) else None,
            response_top_level_keys=sorted(response)))
    selected = [r for sid in latest.values() for r in by_snapshot[sid]]
    baseline = [r for r in selected if r["role"] == "baseline"]
    changes = [c for h in (1, 3, 7) for c in exact_changes(baseline, h)]
    # Comparisons are empirical, not proof that identical histories ignore a filter.
    contrasts = []
    for snap in snapshots:
        if not snap["role"].startswith("contrast_"):
            continue
        field = snap["role"].removeprefix("contrast_")
        for base in snapshots:
            if base["role"] != "baseline":
                continue
            if {k: v for k, v in base["params"].items() if k != field} != {k: v for k, v in snap["params"].items() if k != field}:
                continue
            a = {r["historical_timestamp"]: r["price"] for r in by_snapshot[base["snapshot_id"]]}
            b = {r["historical_timestamp"]: r["price"] for r in by_snapshot[snap["snapshot_id"]]}
            overlap = a.keys() & b.keys()
            contrasts.append(dict(baseline_snapshot=base["snapshot_id"], contrast_snapshot=snap["snapshot_id"],
                field=field, overlapping_timestamps=len(overlap), differing_prices=sum(a[t] != b[t] for t in overlap)))
    result = dict(status="NO_DATA" if not snapshots else "PROVISIONAL_AUDIT_REQUIRES_SEMANTIC_REVIEW",
        snapshot_count=len(snapshots), query_count=len({s["search_id"] for s in snapshots}),
        attempted_baseline_trip_count=len({(s["params"]["departure_id"], s["params"]["arrival_id"], s["params"]["outbound_date"])
                                           for s in snapshots if s["role"] == "baseline"}),
        successful_snapshot_count=sum(s["outcome"] == "success" for s in snapshots),
        snapshots_with_history=sum(s["parsed_rows"] > 0 for s in summaries),
        independent_oneway_trips_with_history=len({r['trip_id'] for r in all_rows if r['trip_type'] == 2 and r['eligible']}),
        independent_roundtrip_controls_with_history=len({r['trip_id'] for r in all_rows if r['trip_type'] == 1 and r['eligible']}),
        missing_history_snapshot_count=sum("missing_history" in s["issues"] for s in summaries),
        baseline_independent_trip_count=len({r["trip_id"] for r in baseline}),
        usable_baseline_daily_observations=len(baseline),
        horizon_pair_counts={str(h): sum(c["horizon_days"] == h for c in changes) for h in (1, 3, 7)},
        snapshots=summaries, filter_comparisons=contrasts, revisions=revision_audit(all_rows),
        timezone_convention=OBSERVATION_ZONE, timezone_verified=False,
        note="Usable means structurally usable, not validated qualifying fares. Latest successful snapshot per query for descriptive audit only. No predictive point-in-time guarantee.")
    atomic_json(root / "normalized/observations.json", all_rows)
    atomic_json(root / "processed/daily.json", baseline)
    atomic_json(root / "processed/changes.json", changes)
    atomic_json(root / "processed/feasibility.json", result)
    return result


if __name__ == "__main__":
    result = audit()
    print(json.dumps({k: v for k, v in result.items() if k not in {"snapshots", "revisions", "filter_comparisons"}}, indent=2))

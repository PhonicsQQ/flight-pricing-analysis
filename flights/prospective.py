"""Dry-run by default; one manually requested future checkpoint search at a time."""
import argparse
from datetime import datetime
import json
import os
from zoneinfo import ZoneInfo
from flights.collect import ROOT, collect, load_env, query_id, validate_plan


def checkpoint(protocol, instant):
    local=instant.astimezone(ZoneInfo(protocol['timezone']))
    planned={r['date']:r for r in protocol['checkpoints']}
    if local.date().isoformat() not in planned:
        raise ValueError('Not a planned collection date; no search permitted')
    clock=local.strftime('%H:%M')
    start,end=protocol['local_time_window']
    if not start<=clock<end:
        raise ValueError('Outside the planned local-time window; no search permitted')
    return planned[local.date().isoformat()]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--only',help='One query ID printed by dry run')
    args=parser.parse_args()
    protocol=json.loads((ROOT/'config/prospective-protocol.json').read_text())
    plan=json.loads((ROOT/protocol['query_manifest']).read_text())
    validate_plan(plan)
    ids={query_id(q['params']):q['params']['arrival_id'] for q in plan['queries']}
    if not args.live:
        print('DRY RUN: no credentials, requests, or scheduling')
        print(json.dumps(dict(checkpoints=protocol['checkpoints'],timezone=protocol['timezone'],
                              window=protocol['local_time_window'],queries=ids,planned_attempts=9),indent=2))
        return
    checkpoint(protocol,datetime.now(ZoneInfo(protocol['timezone'])))
    if args.only not in ids:
        raise ValueError('Specify one valid --only query ID')
    load_env()
    key=os.environ.get('SERPAPI_API_KEY','')
    if not key or os.environ.get('SERPAPI_FREE_PLAN_CONFIRMED','').lower()!='true':
        raise ValueError('Configure credentials and free-plan confirmation locally')
    # Existing durable ledger, quota check, lock, and >=24-hour refresh rule all apply.
    collect(plan,key,limit=1,refresh=True,only=args.only)


if __name__=='__main__':
    main()

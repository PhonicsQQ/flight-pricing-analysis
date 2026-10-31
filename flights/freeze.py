"""Freeze analysis inputs and provenance without modifying source files."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / 'data/frozen/2026-10-30-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze():
    if (FROZEN / 'manifest.json').exists():
        verify()
        return
    FROZEN.mkdir(parents=True, exist_ok=True)
    inputs = {}
    for name in ('study-daily.json', 'study-changes.json', 'study-coverage.json', 'study-summary.json'):
        source = ROOT / 'data/processed' / name
        target = FROZEN / name
        if target.exists() and sha(target) != sha(source):
            raise RuntimeError('Incomplete freeze conflicts with current data; inspect manually')
        shutil.copyfile(source, target)
        inputs[name] = sha(target)
    shutil.copyfile(ROOT / 'config/study.json', FROZEN / 'study-manifest.json')
    inputs['study-manifest.json'] = sha(FROZEN / 'study-manifest.json')
    coverage = json.loads((FROZEN / 'study-coverage.json').read_text())
    raw = {r['snapshot_id']: sha(ROOT / 'data/raw' / (r['snapshot_id']+'.json')) for r in coverage}
    manifest = dict(version='2026-10-30-v1', frozen_at=datetime.now(timezone.utc).isoformat(),
                    input_sha256=inputs, raw_snapshot_sha256=raw,
                    note='Local research freeze; checksums detect mutation. Not a public data license.')
    (FROZEN / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    verify()


def verify():
    m = json.loads((FROZEN / 'manifest.json').read_text())
    for name, digest in m['input_sha256'].items():
        if sha(FROZEN / name) != digest:
            raise RuntimeError('Frozen input changed: '+name)
    for sid, digest in m['raw_snapshot_sha256'].items():
        if sha(ROOT / 'data/raw' / (sid+'.json')) != digest:
            raise RuntimeError('Frozen source snapshot changed: '+sid)
    return m


if __name__ == '__main__':
    freeze()
    print('Frozen inputs and 168 referenced raw snapshots verified:', FROZEN)

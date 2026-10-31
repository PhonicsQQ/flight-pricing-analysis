"""Synthetic checks of research weighting and frozen-input integrity."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from flights import freeze

try:
    import pandas as pd
    from flights.analyze import summarize, weekday_standardized, bucket
except ImportError:
    pd = None


class FreezeTests(unittest.TestCase):
    def test_mutated_frozen_input_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'input.json'
            source.write_text('[]')
            (root / 'manifest.json').write_text(json.dumps(dict(
                input_sha256={'input.json': freeze.sha(source)}, raw_snapshot_sha256={})))
            with patch.object(freeze, 'FROZEN', root):
                freeze.verify()
                source.write_text('[1]')
                with self.assertRaisesRegex(RuntimeError, 'Frozen input changed'):
                    freeze.verify()


@unittest.skipIf(pd is None, 'Install analysis dependencies for statistical tests')
class AnalysisTests(unittest.TestCase):
    def test_unequal_histories_receive_equal_weight(self):
        rows = [dict(search_id='a', change_usd=10, change_percent=10,
                     destination='ATL', departure_date='2026-10-31') for _ in range(10)]
        rows.append(dict(search_id='b', change_usd=-10, change_percent=-10,
                         destination='ATL', departure_date='2026-11-07'))
        result = summarize(pd.DataFrame(rows), 'fixture')
        self.assertEqual(result['trip_up'], .5)
        self.assertEqual(result['mean_usd'], 0)
        self.assertAlmostEqual(result['row_up'], 10/11)
        self.assertEqual(result, summarize(pd.DataFrame(rows), 'fixture'))

    def test_sparse_weekdays_not_standardized(self):
        data = pd.DataFrame([dict(search_id='a', change_usd=10, destination='ATL',
                                 days_until_departure=12, observation_weekday='Monday')])
        data['lead_bucket'] = bucket(data.days_until_departure)
        result = weekday_standardized(data, 'observation_weekday')
        self.assertEqual(result['common_cells'], 0)
        self.assertEqual(result['rates'], {})

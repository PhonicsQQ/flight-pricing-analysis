"""Synthetic snapshot comparison; never a real research series."""
import unittest
from copy import deepcopy
from test_pipeline import snapshot, ts
from flights.refresh_report import compare


class RefreshTests(unittest.TestCase):
    def test_additions_removals_and_revisions_are_distinct(self):
        old = snapshot([[ts('2026-11-01'), 100], [ts('2026-11-02'), 120], [ts('2026-11-03'), 130]])
        new = deepcopy(old)
        new['snapshot_id'] = 'new'
        new['response']['price_insights']['price_history'] = [
            [ts('2026-11-02'), 110], [ts('2026-11-03'), 130], [ts('2026-11-04'), 140]]
        result = compare(old, new)
        self.assertEqual(result['overlapping_timestamps'], 2)
        self.assertEqual(len(result['revisions']), 1)
        self.assertEqual(result['revisions'][0]['old_price'], 120)
        self.assertEqual(len(result['added']), 1)
        self.assertEqual(len(result['dropped']), 1)
        self.assertEqual(old['response']['price_insights']['price_history'][1][1], 120)

    def test_missing_refresh_history_is_not_zero(self):
        old = snapshot([[ts('2026-11-01'), 100]])
        new = deepcopy(old)
        new['response'] = {}
        result = compare(old, new)
        self.assertIsNone(result['refreshed_last'])
        self.assertIn('missing_history', result['refreshed_issues'])
        self.assertEqual(result['revisions'], [])

from datetime import datetime, timezone
import json
import unittest
from flights.collect import ROOT, validate_plan
from flights.prospective import checkpoint

class ProspectiveTests(unittest.TestCase):
    def setUp(self):
        self.p=json.loads((ROOT/'config/prospective-protocol.json').read_text())

    def test_window_and_timezone_guard(self):
        # November dates are standard time: 17:00 UTC is noon Eastern.
        self.assertEqual(checkpoint(self.p,datetime(2026,11,12,17,0,tzinfo=timezone.utc))['lead_days'],15)
        for stamp in [datetime(2026,11,5,17,tzinfo=timezone.utc),
                      datetime(2026,11,12,16,59,tzinfo=timezone.utc),
                      datetime(2026,11,12,17,30,tzinfo=timezone.utc)]:
            with self.assertRaises(ValueError):checkpoint(self.p,stamp)

    def test_budget_and_supported_queries(self):
        plan=json.loads((ROOT/self.p['query_manifest']).read_text())
        validate_plan(plan)
        self.assertEqual(len(plan['queries'])*len(self.p['checkpoints']),9)
        self.assertLessEqual(self.p['planned_attempts']+self.p['retry_reserve'],10)
        self.assertEqual(self.p['lifetime_cap'],200)

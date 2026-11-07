import unittest
from flights.mean_audit import audit_changes

class MeanAuditTests(unittest.TestCase):
    def test_extreme_changes_retained_and_sign_flip_detected(self):
        values=[-10,-10,100]
        r=audit_changes(values)
        self.assertAlmostEqual(r['mean'],80/3)
        self.assertEqual(r['without_largest'],-10)
        self.assertTrue(r['sign_can_flip'])
        self.assertEqual(values,[-10,-10,100])

    def test_empty_and_singleton_do_not_invent_sensitivity(self):
        self.assertIsNone(audit_changes([]))
        r=audit_changes([10])
        self.assertIsNone(r['without_largest'])
        self.assertIsNone(r['without_largest_10pct'])
        self.assertTrue(r['small_sample'])

"""Tests for the known-issues suppression mechanism (BL-5)."""
from django.test import SimpleTestCase

from .known_issues import effective_cap


class EffectiveCapTests(SimpleTestCase):
    """effective_cap() resolves an endpoint's budget, honoring KNOWN_ISSUES."""

    def test_known_issue_uses_cap(self):
        budgets = {'Export': 45}
        issues = {'Export': {'cap': 60, 'ticket': 't', 'note': 'n'}}
        cap, issue = effective_cap('Export', budgets, issues)
        self.assertEqual(cap, 60)
        self.assertIsNotNone(issue)

    def test_no_issue_uses_budget(self):
        budgets = {'Export': 45}
        cap, issue = effective_cap('Export', budgets, {})
        self.assertEqual(cap, 45)
        self.assertIsNone(issue)

    def test_missing_endpoint_raises(self):
        with self.assertRaises(KeyError):
            effective_cap('Nope', {}, {})

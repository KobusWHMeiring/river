"""Known over-budget endpoints (BL-5).

When an endpoint legitimately exceeds its BUDGETS baseline and the extra
queries cannot be removed, record it here instead of raising the budget or
commenting out the test. Each entry gives the endpoint a higher effective cap
while the ticket is open: the budget test still runs and still fails if the
endpoint blows past the cap, but a known, tracked overage is tolerated.

Entry shape (key must match a BUDGETS key in base.py):

    '<endpoint name>': {
        'cap': <int>,        # tolerated query count while the ticket is open
        'ticket': '<path>',  # tracking doc (e.g. product/refinement/...)
        'note': '<why>',     # one-line reason the overage is acceptable
    }

No entries today — every endpoint is within budget.
"""
KNOWN_ISSUES = {}


def effective_cap(endpoint, budgets, known_issues=None):
    """Return (cap, issue) for an endpoint.

    If the endpoint is a known issue, cap is the issue's tolerated cap;
    otherwise cap is the endpoint's normal budget. `issue` is the
    KNOWN_ISSUES entry (dict) when suppressed, else None.
    """
    issues = known_issues if known_issues is not None else KNOWN_ISSUES
    issue = issues.get(endpoint)
    if issue is not None:
        return issue['cap'], issue
    return budgets[endpoint], None

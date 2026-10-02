from src.analytics_workspace import CaseMetric, summarize_cases, status_breakdown, policy_breakdown, compare_periods, average_analyst_minutes, coverage_buckets

def rows():
    return [
        CaseMetric("org-a", "c1", "HUMAN_REVIEW", ("RD-P01", "RD-P03"), 3, 2, 80, 30, 1, 0, 1),
        CaseMetric("org-a", "c2", "READY_TO_SUBMIT", ("RD-P01",), 2, 4, 100, 20, 1, 1, 1),
        CaseMetric("org-b", "c3", "CLOSED", ("RD-P08",), 1, 1, 40, 10, 0, 0, 1),
    ]

def test_tenant_summary():
    assert summarize_cases(rows(), organization_id="org-a") == {"cases":2,"claims":5,"evidence":6,"submissions":2,"appeals":1,"outcomes":2,"analyst_minutes":50,"avg_evidence_coverage":90.0}

def test_tenant_isolation():
    assert summarize_cases(rows(), organization_id="org-b")["cases"] == 1
    assert status_breakdown(rows(), organization_id="org-a") == {"HUMAN_REVIEW":1,"READY_TO_SUBMIT":1}

def test_policy_breakdown():
    assert policy_breakdown(rows(), organization_id="org-a") == {"RD-P01":2,"RD-P03":1}

def test_period_comparison():
    result = compare_periods({"cases":12,"appeals":2},{"cases":10,"appeals":4})
    assert result["cases"] == {"current":12,"previous":10,"delta":2,"percent_change":20.0}
    assert result["appeals"]["delta"] == -2

def test_zero_previous():
    assert compare_periods({"cases":3},{"cases":0})["cases"]["percent_change"] == 0.0

def test_average_time():
    assert average_analyst_minutes(rows(), organization_id="org-a") == 25.0

def test_coverage_buckets():
    assert coverage_buckets(rows(), organization_id="org-a") == {"0-49":0,"50-79":0,"80-99":1,"100":1}

def test_required_tenant():
    try: summarize_cases(rows(), organization_id="")
    except ValueError: pass
    else: raise AssertionError("missing tenant must fail")

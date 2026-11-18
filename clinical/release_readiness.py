"""Fail-closed release readiness for fictional research evaluation artifacts."""
from .reproducible_report import verify_report

def assess_release(report: dict, regression: dict | None = None,
                   *, regression_required: bool = True) -> dict:
    """Evaluate artifact process readiness, never clinical validity."""
    blockers: list[str] = []
    checks = []
    verified = verify_report(report)
    checks.append({"name": "report_integrity", "passed": verified})
    if not verified:
        blockers.append("report_integrity_failed")
        return {"status": "blocked", "checks": checks, "blockers": blockers,
                "disclaimer": "Research process readiness is not clinical validation."}
    gates = report.get("quality_gates")
    quality_ok = isinstance(gates, dict) and gates.get("status") == "pass" and all(
        isinstance(item, dict) and item.get("passed") is True
        for item in gates.get("checks", [])
    ) and bool(gates.get("checks"))
    checks.append({"name": "human_review_quality", "passed": quality_ok})
    if not quality_ok:
        blockers.append("human_review_quality_blocked")
    if regression is None:
        regression_ok = not regression_required
        checks.append({"name": "regression_comparison", "passed": regression_ok,
                       "reason": "not_provided"})
        if regression_required:
            blockers.append("regression_comparison_missing")
    else:
        valid = (isinstance(regression, dict) and
                 regression.get("current_sha256") == report.get("report_sha256") and
                 regression.get("status") == "pass" and
                 regression.get("blockers") == [] and
                 isinstance(regression.get("baseline_sha256"), str) and
                 len(regression["baseline_sha256"]) == 64)
        checks.append({"name": "regression_comparison", "passed": valid})
        if not valid:
            blockers.append("regression_comparison_failed")
    return {"status": "ready_for_manual_research_review" if not blockers else "blocked",
            "checks": checks, "blockers": blockers,
            "report_sha256": report["report_sha256"],
            "disclaimer": "Research process readiness is not clinical validation or approval."}

import json
from datetime import datetime

def generate_review_report(
    repo_url: str,
    bugs: list[dict],           # from Week 3 BugDetector
    fixes: list[dict],          # from Week 3 FixGenerator
    vulnerabilities: list[dict],# from Week 3 VulnerabilityScanner (Person 3)
    generated_tests: list[dict],# from Week 4 TestGenerator
    coverage_before: float,
    coverage_after: float,
) -> dict:
    
    report = {
        "meta": {
            "repo_url": repo_url,
            "generated_at": datetime.now().isoformat(),
            "agent_version": "1.0.0"
        },
        "summary": {
            "total_bugs": len(bugs),
            "bugs_by_severity": {
                "critical": len([b for b in bugs if b["severity"] == "critical"]),
                "high":     len([b for b in bugs if b["severity"] == "high"]),
                "medium":   len([b for b in bugs if b["severity"] == "medium"]),
                "low":      len([b for b in bugs if b["severity"] == "low"]),
            },
            "fixes_validated": len([f for f in fixes if f["validation"]["passed"]]),
            "vulnerabilities_found": len(vulnerabilities),
            "coverage_before": coverage_before,
            "coverage_after": coverage_after,
            "coverage_improvement": round(coverage_after - coverage_before, 2)
        },
        "bugs": bugs,
        "fixes": fixes,
        "vulnerabilities": vulnerabilities,
        "generated_tests": generated_tests,
    }
    
    # Save to file
    with open("review_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report
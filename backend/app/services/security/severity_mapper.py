"""
CoDude — OWASP Severity Mapper (Day 11)

Maps OWASP Top 10 categories to default severity levels and provides
severity-based sorting for SecurityFinding objects.

Severity levels (descending order):
    critical → high → medium → low → info

The severity_order dict assigns numeric weights for sorting:
    critical = 0 (highest priority), info = 4 (lowest priority)

Usage:
    from app.services.security.severity_mapper import (
        get_default_severity,
        sort_findings_by_severity,
        SEVERITY_ORDER,
    )

    severity = get_default_severity("A03:2021 - Injection")  # → "critical"
    sorted_findings = sort_findings_by_severity(findings)
"""

# ── Severity order for sorting (lower = more severe) ─────────────────────────

SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

# ── OWASP category → default severity mapping ───────────────────────────────

OWASP_SEVERITY_MAP: dict[str, str] = {
    # A01:2021 — Broken Access Control
    "A01:2021 - Broken Access Control": "critical",
    # A02:2021 — Cryptographic Failures
    "A02:2021 - Cryptographic Failures": "high",
    # A03:2021 — Injection (includes XSS)
    "A03:2021 - Injection": "critical",
    "A03:2021 - Cross-Site Scripting (XSS)": "high",
    # A04:2021 — Insecure Design
    "A04:2021 - Insecure Design": "medium",
    # A05:2021 — Security Misconfiguration
    "A05:2021 - Security Misconfiguration": "medium",
    # A06:2021 — Vulnerable and Outdated Components
    "A06:2021 - Vulnerable and Outdated Components": "high",
    # A07:2021 — Identification and Authentication Failures
    "A07:2021 - Identification and Authentication Failures": "high",
    # A08:2021 — Software and Data Integrity Failures
    "A08:2021 - Software and Data Integrity Failures": "critical",
    # A09:2021 — Security Logging and Monitoring Failures
    "A09:2021 - Security Logging and Monitoring Failures": "medium",
    # A10:2021 — Server-Side Request Forgery (SSRF)
    "A10:2021 - Server-Side Request Forgery (SSRF)": "high",
}


def get_default_severity(owasp_category: str) -> str:
    """Return the default severity for an OWASP category.

    Args:
        owasp_category: OWASP Top 10 category string (e.g., "A03:2021 - Injection").

    Returns:
        Default severity level (critical, high, medium, low, info).
        Falls back to "medium" for unknown categories.
    """
    return OWASP_SEVERITY_MAP.get(owasp_category, "medium")


def sort_findings_by_severity(findings: list) -> list:
    """Sort SecurityFinding objects by severity (critical first).

    Args:
        findings: List of SecurityFinding objects (must have a 'severity' attribute).

    Returns:
        A new list sorted by severity (critical → high → medium → low → info),
        with findings of the same severity ordered by line number.
    """
    return sorted(
        findings,
        key=lambda f: (
            SEVERITY_ORDER.get(f.severity, 99),
            f.line,
        ),
    )

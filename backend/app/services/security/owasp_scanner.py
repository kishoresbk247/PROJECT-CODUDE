"""
CoDude — OWASP Top 10 Security Scanner (Day 10 — Part 1)

Dedicated security scanner covering the first 3 OWASP Top 10 (2021) categories:

    A02:2021 — Cryptographic Failures (Sensitive Data Exposure)
    A03:2021 — Injection (SQL, Command, LDAP, Template)
    A07:2021 — Identification and Authentication Failures

Architecture:
    OWASPScanner aggregates all pattern modules and scans code line-by-line,
    returning SecurityFinding objects with OWASP category, CWE ID, severity,
    and a remediation link for every match.

    This is a pure static-analysis scanner — no LLM calls, no network I/O,
    sub-millisecond per scan.  It complements the existing LLM-based security
    review chain in the pipeline.

Usage:
    scanner = OWASPScanner()
    findings = scanner.scan(code, language="python")

    for f in findings:
        print(f.owasp_category, f.cwe_id, f.message, f.remediation_link)
"""

import logging

from app.services.security.patterns.auth import AUTH_PATTERNS
from app.services.security.patterns.data_exposure import DATA_EXPOSURE_PATTERNS
from app.services.security.patterns.injection import INJECTION_PATTERNS

logger = logging.getLogger(__name__)


class SecurityFinding:
    """Lightweight finding DTO for OWASP scan results.

    Attributes:
        line:              Line number where the finding occurs.
        severity:          Severity level (critical, high, medium, low).
        message:           Human-readable description of the vulnerability.
        suggestion:        Recommended fix or remediation.
        owasp_category:    OWASP Top 10 category identifier.
        cwe_id:            Common Weakness Enumeration identifier.
        remediation_link:  URL to the OWASP reference page.
    """

    __slots__ = (
        "line",
        "severity",
        "message",
        "suggestion",
        "owasp_category",
        "cwe_id",
        "remediation_link",
    )

    def __init__(
        self,
        line: int,
        severity: str,
        message: str,
        suggestion: str,
        owasp_category: str,
        cwe_id: str,
        remediation_link: str,
    ) -> None:
        self.line = line
        self.severity = severity
        self.message = message
        self.suggestion = suggestion
        self.owasp_category = owasp_category
        self.cwe_id = cwe_id
        self.remediation_link = remediation_link

    def __repr__(self) -> str:
        return (
            f"SecurityFinding(line={self.line}, severity='{self.severity}', "
            f"cwe='{self.cwe_id}', owasp='{self.owasp_category}')"
        )


class OWASPScanner:
    """
    OWASP Top 10 Security Scanner — Part 1.

    Scans source code against compiled regex patterns for the first 5
    OWASP Top 10 categories (A02, A03, A07).  Returns a list of
    SecurityFinding objects with full OWASP metadata.

    Supported languages: python, javascript, java
    (Patterns are language-aware where applicable; most patterns target
    Python-specific sinks like cursor.execute(), os.system(), etc.)

    Performance:
        All patterns are pre-compiled at import time.  Scanning 1,000
        lines takes <1ms on modern hardware.
    """

    def __init__(self) -> None:
        """Initialize the scanner with all registered pattern modules."""
        # Aggregate all patterns from all OWASP categories
        self._patterns: list[dict] = (
            INJECTION_PATTERNS + AUTH_PATTERNS + DATA_EXPOSURE_PATTERNS
        )
        logger.info(
            "OWASPScanner initialized with %d patterns across 3 OWASP categories",
            len(self._patterns),
        )

    def scan(self, code: str, language: str = "python") -> list[SecurityFinding]:
        """
        Scan source code for OWASP Top 10 vulnerabilities.

        Args:
            code:     Source code as a string.
            language: Programming language (currently used for logging;
                      patterns are applied universally since injection
                      sinks are often language-specific in the patterns).

        Returns:
            A list of SecurityFinding objects, one per match, each with
            OWASP category, CWE ID, and remediation link populated.
            Returns an empty list if no vulnerabilities are found.
        """
        findings: list[SecurityFinding] = []
        lines = code.splitlines()

        for line_number, line_text in enumerate(lines, start=1):
            # Skip empty / whitespace-only lines
            stripped = line_text.strip()
            if not stripped:
                continue

            # Skip single-line comments
            if stripped.startswith("#") or stripped.startswith("//"):
                continue

            for pattern_entry in self._patterns:
                if pattern_entry["pattern"].search(line_text):
                    findings.append(
                        SecurityFinding(
                            line=line_number,
                            severity=pattern_entry["severity"],
                            message=pattern_entry["message"],
                            suggestion=pattern_entry["suggestion"],
                            owasp_category=pattern_entry["owasp_category"],
                            cwe_id=pattern_entry["cwe_id"],
                            remediation_link=pattern_entry["remediation_link"],
                        )
                    )

        logger.info(
            "OWASPScanner found %d issue(s) in %s code (%d lines)",
            len(findings),
            language,
            len(lines),
        )
        return findings

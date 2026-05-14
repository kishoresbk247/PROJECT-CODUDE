"""
CoDude — OWASP Security Scanner Package (Day 10 + Day 11)

Complete security scanner covering all OWASP Top 10 (2021) categories:

    A02:2021 — Cryptographic Failures (Sensitive Data Exposure)
    A03:2021 — Injection (SQL, Command, LDAP, Template)
    A03:2021 — Cross-Site Scripting (XSS)
    A05:2021 — Security Misconfiguration
    A07:2021 — Identification and Authentication Failures
    A08:2021 — Software and Data Integrity Failures (Insecure Deserialization)
    A10:2021 — Server-Side Request Forgery (SSRF)

Pattern modules:
    - injection.py:       SQL, command, LDAP, and template injection patterns
    - auth.py:            Hardcoded credentials, weak hashing, missing auth decorators
    - data_exposure.py:   HTTP URLs, sensitive data logging, unencrypted DB connections
    - xss.py:             innerHTML, dangerouslySetInnerHTML, document.write, render+GET
    - misconfig.py:       DEBUG=True, CORS wildcard, verify=False, default secrets
    - deserialization.py: pickle.loads, yaml.load, eval, exec
    - ssrf.py:            requests.get(url), urllib.urlopen, httpx/aiohttp

All patterns return list[SecurityFinding] with OWASP category, CWE ID, and
remediation links for professional-grade reporting.
"""

from app.services.security.owasp_scanner import OWASPScanner
from app.services.security.severity_mapper import (
    get_default_severity,
    sort_findings_by_severity,
    SEVERITY_ORDER,
)

__all__ = [
    "OWASPScanner",
    "get_default_severity",
    "sort_findings_by_severity",
    "SEVERITY_ORDER",
]

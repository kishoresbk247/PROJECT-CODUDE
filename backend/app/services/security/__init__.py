"""
CoDude — OWASP Security Scanner Package (Day 10)

Dedicated security scanner covering the first 5 OWASP Top 10 (2021) categories:

    A02:2021 — Cryptographic Failures (Sensitive Data Exposure)
    A03:2021 — Injection (SQL, Command, LDAP, Template)
    A07:2021 — Identification and Authentication Failures

Pattern modules:
    - injection.py:      SQL, command, LDAP, and template injection patterns
    - auth.py:           Hardcoded credentials, weak hashing, missing auth decorators
    - data_exposure.py:  HTTP URLs, sensitive data logging, unencrypted DB connections

All patterns return list[SecurityFinding] with OWASP category, CWE ID, and
remediation links for professional-grade reporting.
"""

from app.services.security.owasp_scanner import OWASPScanner

__all__ = ["OWASPScanner"]

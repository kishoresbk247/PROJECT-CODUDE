"""
CoDude — A02:2021 Cryptographic Failures Patterns (Day 10)

Regex patterns for detecting sensitive data exposure:

    1. HTTP URLs in API Calls (CWE-319) — http:// in requests/fetch/urllib calls
    2. Logging Sensitive Data  (CWE-532) — logger/print outputting passwords/tokens/secrets
    3. Unencrypted DB Connections (CWE-311) — database URIs without SSL/TLS

Pattern design for low false positives:
    - HTTP patterns exclude localhost/127.0.0.1 (development URLs)
    - Logging patterns require both a log function AND a sensitive keyword
    - DB patterns target connection strings with recognizable schemes

References:
    https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
"""

import re

# ── OWASP metadata ───────────────────────────────────────────────────────────
OWASP_CATEGORY = "A02:2021 - Cryptographic Failures"
OWASP_LINK = "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/"

# ── Pattern Definitions ──────────────────────────────────────────────────────

DATA_EXPOSURE_PATTERNS: list[dict] = [
    # ── 1. HTTP URL in API calls ─────────────────────────────────────────
    {
        "pattern": re.compile(
            r"""\b(?:requests\.(?:get|post|put|patch|delete)|"""
            r"""fetch|urllib\.request\.urlopen)\s*\(\s*"""
            r"""(?:f?['"])http://(?!(?:localhost|127\.0\.0\.1|0\.0\.0\.0))""",
            re.IGNORECASE,
        ),
        "message": (
            "Insecure HTTP: API call using http:// instead of https://. "
            "Data transmitted over HTTP is sent in plaintext and can be "
            "intercepted, modified, or replayed by network attackers (MITM)."
        ),
        "severity": "high",
        "cwe_id": "CWE-319",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use https:// for all API calls. If the server doesn't support "
            "TLS, request a certificate from Let's Encrypt (free). "
            "Enforce HTTPS in production via HSTS headers."
        ),
    },
    # ── 2. HTTP URL in string assignment ─────────────────────────────────
    {
        "pattern": re.compile(
            r"""(?:url|endpoint|api_url|base_url|host)\s*=\s*"""
            r"""(?:f?['"])http://(?!(?:localhost|127\.0\.0\.1|0\.0\.0\.0))""",
            re.IGNORECASE,
        ),
        "message": (
            "Insecure HTTP: URL variable assigned an http:// address. "
            "API endpoints using unencrypted HTTP expose credentials, tokens, "
            "and sensitive data to network eavesdroppers."
        ),
        "severity": "high",
        "cwe_id": "CWE-319",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Change http:// to https://. Store base URLs in environment "
            "variables so production always uses HTTPS even if dev uses HTTP."
        ),
    },
    # ── 3. Logging passwords ─────────────────────────────────────────────
    {
        "pattern": re.compile(
            r"""\b(?:logger\.(?:info|debug|warning|error|critical)|"""
            r"""logging\.(?:info|debug|warning|error|critical)|"""
            r"""print)\s*\(.*\b(?:password|passwd|pwd)\b""",
            re.IGNORECASE,
        ),
        "message": (
            "Sensitive Data Logging: password value written to logs. "
            "Passwords in log files are accessible to anyone with log access "
            "and persist long after the user changes their password."
        ),
        "severity": "high",
        "cwe_id": "CWE-532",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Never log passwords, tokens, or secrets. Use a redaction filter: "
            "logger.info('User %s authenticated', username) — log the event, "
            "not the credential."
        ),
    },
    # ── 4. Logging tokens / secrets ──────────────────────────────────────
    {
        "pattern": re.compile(
            r"""\b(?:logger\.(?:info|debug|warning|error|critical)|"""
            r"""logging\.(?:info|debug|warning|error|critical)|"""
            r"""print)\s*\(.*\b(?:token|secret|api_key|access_key|private_key)\b""",
            re.IGNORECASE,
        ),
        "message": (
            "Sensitive Data Logging: token or secret written to logs. "
            "Tokens in log files can be harvested to impersonate users "
            "or access protected resources."
        ),
        "severity": "high",
        "cwe_id": "CWE-532",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Mask sensitive values before logging: "
            "logger.info('Token: %s...', token[:4]). Better yet, log only "
            "the event ('Token refreshed') without the value."
        ),
    },
    # ── 5. Unencrypted database connection (MySQL) ───────────────────────
    {
        "pattern": re.compile(
            r"""(?:mysql|postgresql|postgres|mariadb)://[^'"\s]*(?!.*ssl)""",
            re.IGNORECASE,
        ),
        "message": (
            "Unencrypted Database Connection: database URI without SSL/TLS. "
            "Database traffic over unencrypted connections exposes query data, "
            "credentials, and results to network interception."
        ),
        "severity": "high",
        "cwe_id": "CWE-311",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Add ?sslmode=require (PostgreSQL) or ?ssl=true (MySQL) to the "
            "connection string. Configure the database server to require TLS "
            "for all client connections."
        ),
    },
]

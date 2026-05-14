"""
CoDude — A05:2021 Security Misconfiguration Patterns (Day 11)

Regex patterns for detecting security misconfigurations:

    1. DEBUG Mode Enabled      (CWE-489) — DEBUG = True in non-test files
    2. CORS Wildcard Origin    (CWE-942) — allow_origins=["*"]
    3. SSL Verification Off    (CWE-295) — verify=False in HTTP requests
    4. Default Django Secret   (CWE-798) — SECRET_KEY = "django-insecure-..."
    5. Default JWT Secret      (CWE-798) — JWT_SECRET = "secret" / "changeme"

Pattern design for low false positives:
    - DEBUG = True is only dangerous in production config files, but since
      we can't determine the deployment context from regex alone, we flag it
      as medium severity with a suggestion to use environment variables
    - CORS wildcard is always flagged — even in development, it creates
      bad habits that often leak into production
    - verify=False explicitly disables SSL cert validation, making MITM trivial

References:
    https://owasp.org/Top10/A05_2021-Security_Misconfiguration/
"""

import re

# ── OWASP metadata ───────────────────────────────────────────────────────────
OWASP_CATEGORY = "A05:2021 - Security Misconfiguration"
OWASP_LINK = "https://owasp.org/Top10/A05_2021-Security_Misconfiguration/"

# ── Pattern Definitions ──────────────────────────────────────────────────────

MISCONFIG_PATTERNS: list[dict] = [
    # ── 1. DEBUG mode enabled ────────────────────────────────────────────
    {
        "pattern": re.compile(
            r"""\bDEBUG\s*=\s*True\b""",
        ),
        "message": (
            "Security Misconfiguration: DEBUG = True detected. Debug mode "
            "exposes detailed stack traces, database queries, and internal "
            "configuration to end users. In Django, it also serves static "
            "files and disables several security checks."
        ),
        "severity": "medium",
        "cwe_id": "CWE-489",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Set DEBUG via environment variable: "
            "DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'. "
            "Never hardcode DEBUG = True in files that are deployed to production."
        ),
    },
    # ── 2. CORS wildcard origin ──────────────────────────────────────────
    {
        "pattern": re.compile(
            r"""allow_origins\s*=\s*\[\s*["']\*["']\s*\]""",
        ),
        "message": (
            "Security Misconfiguration: CORS allow_origins=['*'] allows "
            "any website to make cross-origin requests to this API. "
            "Attackers can exploit this to steal user data via malicious "
            "websites that make authenticated requests on behalf of victims."
        ),
        "severity": "medium",
        "cwe_id": "CWE-942",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Restrict CORS to known origins: "
            "allow_origins=['https://yourdomain.com', 'https://app.yourdomain.com']. "
            "Use environment variables to configure allowed origins per environment."
        ),
    },
    # ── 3. SSL verification disabled ─────────────────────────────────────
    {
        "pattern": re.compile(
            r"""\b(?:requests\.(?:get|post|put|patch|delete|head|options)|"""
            r"""httpx\.(?:get|post|put|patch|delete|head|options))\s*\("""
            r""".*verify\s*=\s*False""",
        ),
        "message": (
            "Security Misconfiguration: SSL verification disabled (verify=False). "
            "Disabling certificate verification allows man-in-the-middle attacks — "
            "an attacker on the network can intercept, read, and modify all HTTPS "
            "traffic between this application and the remote server."
        ),
        "severity": "high",
        "cwe_id": "CWE-295",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Remove verify=False. If using a self-signed certificate, "
            "pass the CA bundle path instead: verify='/path/to/ca-bundle.crt'. "
            "In development, use mkcert to generate locally-trusted certificates."
        ),
    },
    # ── 4. Default Django insecure secret key ────────────────────────────
    {
        "pattern": re.compile(
            r"""SECRET_KEY\s*=\s*['"]django-insecure-""",
        ),
        "message": (
            "Security Misconfiguration: Default Django insecure SECRET_KEY detected. "
            "The 'django-insecure-' prefix is Django's warning that this key is not "
            "suitable for production. It's used for session signing, CSRF tokens, "
            "and password reset tokens — a known key compromises all of these."
        ),
        "severity": "critical",
        "cwe_id": "CWE-798",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Generate a secure key: python -c \"from django.core.management.utils "
            "import get_random_secret_key; print(get_random_secret_key())\". "
            "Store it in an environment variable: SECRET_KEY = os.environ['SECRET_KEY']."
        ),
    },
    # ── 5. Default JWT secret ────────────────────────────────────────────
    {
        "pattern": re.compile(
            r"""(?:JWT_SECRET|JWT_SECRET_KEY)\s*=\s*['"]"""
            r"""(?:secret|changeme|password|jwt_secret|your-secret-key)['"]""",
            re.IGNORECASE,
        ),
        "message": (
            "Security Misconfiguration: Default/weak JWT secret detected. "
            "Common secrets like 'secret' or 'changeme' can be trivially guessed "
            "or brute-forced, allowing attackers to forge valid JWT tokens and "
            "impersonate any user."
        ),
        "severity": "critical",
        "cwe_id": "CWE-798",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Generate a cryptographically random secret: "
            "python -c \"import secrets; print(secrets.token_hex(32))\". "
            "Store in an environment variable: JWT_SECRET = os.environ['JWT_SECRET']. "
            "Use at least 256 bits of entropy."
        ),
    },
]

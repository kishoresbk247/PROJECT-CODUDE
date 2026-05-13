"""
CoDude — A07:2021 Identification and Authentication Failures Patterns (Day 10)

Regex patterns for detecting authentication weaknesses:

    1. Hardcoded Credentials  (CWE-798) — password/secret/api_key assigned string literals
    2. Weak Password Hashing  (CWE-328) — md5()/sha1() applied to passwords
    3. Missing Auth Decorators (CWE-306) — Flask @login_required / FastAPI Depends absent

Pattern design for low false positives:
    - Credential patterns match assignment to string literals only (not variables)
    - Weak hashing patterns look for md5/sha1 near password-related context
    - Auth decorator detection scans for route decorators without adjacent auth guards

References:
    https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
"""

import re

# ── OWASP metadata ───────────────────────────────────────────────────────────
OWASP_CATEGORY = "A07:2021 - Identification and Authentication Failures"
OWASP_LINK = "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/"

# ── Pattern Definitions ──────────────────────────────────────────────────────

AUTH_PATTERNS: list[dict] = [
    # ── 1. Hardcoded password ────────────────────────────────────────────
    {
        "pattern": re.compile(
            r"""\b(?:password|passwd|pwd)\s*=\s*(['"])(?!\s*\1).+?\1""",
            re.IGNORECASE,
        ),
        "message": (
            "Hardcoded Password: password assigned a string literal. "
            "Hardcoded credentials in source code are trivially extracted "
            "from version control and compiled binaries."
        ),
        "severity": "critical",
        "cwe_id": "CWE-798",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Store credentials in environment variables or a secrets manager "
            "(e.g., AWS Secrets Manager, HashiCorp Vault). "
            "Access via os.environ['DB_PASSWORD'] or a .env file excluded from git."
        ),
    },
    # ── 2. Hardcoded secret key ──────────────────────────────────────────
    {
        "pattern": re.compile(
            r"""\b(?:secret_key|secret|api_secret)\s*=\s*(['"])(?!\s*\1).+?\1""",
            re.IGNORECASE,
        ),
        "message": (
            "Hardcoded Secret Key: secret_key assigned a string literal. "
            "Exposed secrets allow attackers to forge sessions, sign tokens, "
            "and impersonate the application."
        ),
        "severity": "critical",
        "cwe_id": "CWE-798",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use environment variables: SECRET_KEY = os.environ['SECRET_KEY']. "
            "Rotate keys regularly and never commit them to version control."
        ),
    },
    # ── 3. Hardcoded API key ─────────────────────────────────────────────
    {
        "pattern": re.compile(
            r"""\b(?:api_key|apikey|api_token)\s*=\s*(['"])(?!\s*\1).+?\1""",
            re.IGNORECASE,
        ),
        "message": (
            "Hardcoded API Key: api_key assigned a string literal. "
            "Leaked API keys grant unauthorized access to external services "
            "and can incur significant financial charges."
        ),
        "severity": "critical",
        "cwe_id": "CWE-798",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Store API keys in environment variables or a .env file. "
            "Add .env to .gitignore. Use a secrets manager for production."
        ),
    },
    # ── 4. Weak password hashing (MD5) ───────────────────────────────────
    {
        "pattern": re.compile(
            r"""\b(?:hashlib\.)?md5\s*\(""",
        ),
        "message": (
            "Weak Password Hashing: MD5 detected. MD5 is cryptographically "
            "broken — it has known collision attacks and can be brute-forced "
            "at billions of hashes per second on consumer GPUs."
        ),
        "severity": "high",
        "cwe_id": "CWE-328",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use bcrypt, scrypt, or Argon2 for password hashing: "
            "from passlib.hash import bcrypt; hashed = bcrypt.hash(password). "
            "These algorithms are deliberately slow to resist brute-force attacks."
        ),
    },
    # ── 5. Weak password hashing (SHA1) ──────────────────────────────────
    {
        "pattern": re.compile(
            r"""\b(?:hashlib\.)?sha1\s*\(""",
        ),
        "message": (
            "Weak Password Hashing: SHA1 detected. SHA1 has known collision "
            "attacks (SHAttered, 2017) and is far too fast for password "
            "hashing — modern GPUs can compute billions of SHA1 hashes/sec."
        ),
        "severity": "high",
        "cwe_id": "CWE-328",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use bcrypt, scrypt, or Argon2 for password hashing. "
            "For non-password hashing (e.g., checksums), use SHA-256 or SHA-3."
        ),
    },
    # ── 6. Missing auth decorator (Flask route without @login_required) ──
    {
        "pattern": re.compile(
            r"""@(?:app|blueprint|bp)\s*\.(?:route|get|post|put|delete|patch)\s*\("""
        ),
        "message": (
            "Missing Auth Check: Route handler defined without a visible "
            "@login_required decorator. Unprotected endpoints may expose "
            "sensitive data or functionality to unauthenticated users."
        ),
        "severity": "medium",
        "cwe_id": "CWE-306",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Add @login_required (Flask-Login) or Depends(get_current_user) "
            "(FastAPI) to protect this endpoint. If the endpoint is intentionally "
            "public, add a # noqa: auth comment to suppress this warning."
        ),
    },
]

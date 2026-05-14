"""
CoDude — A10:2021 Server-Side Request Forgery (SSRF) Patterns (Day 11)

Regex patterns for detecting SSRF vulnerabilities:

    1. requests.get(url) from parameter  (CWE-918) — URL from function arg
    2. urllib.request.urlopen()           (CWE-918) — URL from variable
    3. httpx/aiohttp with variable URL   (CWE-918) — Async HTTP with user URL

SSRF context-awareness and pattern limits:
    - SSRF is fundamentally about *data flow* — whether a user-controlled value
      reaches an HTTP client. Regex can't track data flow, so we flag the most
      common dangerous patterns: HTTP calls with variable (non-literal) URLs
    - We match requests.get(<variable>) where the first argument is NOT a
      quoted string literal (indicating the URL comes from a variable)
    - We specifically match urllib.request.urlopen() as it's the stdlib's
      most common HTTP function and frequently appears in SSRF vulnerabilities
    - False positives are accepted at medium severity — SSRF detection truly
      requires taint analysis that's beyond regex capabilities

SSRF background (OWASP Top 10 2021 — new category):
    SSRF entered the Top 10 in 2021 driven by cloud infrastructure attacks.
    When a server makes HTTP requests to user-supplied URLs, an attacker can
    point it to internal services — http://169.254.169.254/ is the AWS metadata
    endpoint, which can expose IAM credentials. The fix is an allowlist of
    permitted domains, never a denylist.

References:
    https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/
"""

import re

# ── OWASP metadata ───────────────────────────────────────────────────────────
OWASP_CATEGORY = "A10:2021 - Server-Side Request Forgery (SSRF)"
OWASP_LINK = "https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/"

# ── Pattern Definitions ──────────────────────────────────────────────────────

SSRF_PATTERNS: list[dict] = [
    # ── 1. requests.get/post with variable URL (not string literal) ──────
    {
        "pattern": re.compile(
            r"""\brequests\.(?:get|post|put|patch|delete|head|options)"""
            r"""\s*\(\s*(?!['"`])(?!http)""",
        ),
        "message": (
            "SSRF Risk: HTTP request made with a variable URL. If the URL "
            "originates from user input (request body, query parameter, or "
            "database), an attacker can redirect the server to request internal "
            "resources — including cloud metadata endpoints like "
            "http://169.254.169.254/ which exposes AWS IAM credentials."
        ),
        "severity": "high",
        "cwe_id": "CWE-918",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Validate URLs against an allowlist of permitted domains: "
            "ALLOWED_HOSTS = {'api.example.com', 'cdn.example.com'}; "
            "parsed = urlparse(url); assert parsed.hostname in ALLOWED_HOSTS. "
            "Block private IP ranges (10.x, 172.16-31.x, 192.168.x, 169.254.x). "
            "Never use a denylist — use an allowlist."
        ),
    },
    # ── 2. urllib.request.urlopen() with variable ────────────────────────
    {
        "pattern": re.compile(
            r"""\burllib\.request\.urlopen\s*\(\s*(?!['"`])""",
        ),
        "message": (
            "SSRF Risk: urllib.request.urlopen() called with a variable URL. "
            "urllib does not validate the target host, allowing requests to "
            "internal services, cloud metadata endpoints, and localhost."
        ),
        "severity": "high",
        "cwe_id": "CWE-918",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Validate the URL before opening: parse with urllib.parse.urlparse(), "
            "check hostname against an allowlist, and reject private IP ranges. "
            "Consider using the 'requests' library with a custom transport adapter "
            "that blocks internal addresses."
        ),
    },
    # ── 3. httpx/aiohttp with variable URL ──────────────────────────────
    {
        "pattern": re.compile(
            r"""\b(?:httpx\.(?:get|post|put|patch|delete|head|options|AsyncClient)|"""
            r"""aiohttp\.ClientSession)\s*\(""",
        ),
        "message": (
            "SSRF Risk: HTTP client library usage detected. If the request URL "
            "is derived from user input, this creates an SSRF vector. "
            "Modern async HTTP clients (httpx, aiohttp) are commonly used in "
            "webhook handlers and URL preview features — both prime SSRF targets."
        ),
        "severity": "medium",
        "cwe_id": "CWE-918",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Implement URL validation middleware: "
            "1) Parse and validate against an allowlist of domains. "
            "2) Resolve DNS and reject private/internal IP addresses. "
            "3) Use network-level controls (firewall rules) to prevent "
            "the server from reaching internal resources."
        ),
    },
]

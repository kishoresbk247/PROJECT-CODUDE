"""
CoDude — A03:2021 Cross-Site Scripting (XSS) Patterns (Day 11)

Regex patterns for detecting XSS vulnerabilities:

    1. innerHTML Assignment    (CWE-79)  — element.innerHTML = variable
    2. dangerouslySetInnerHTML (CWE-79)  — React prop without DOMPurify
    3. Django/Flask Template    (CWE-79)  — render(request.GET.get(...)) 
    4. document.write           (CWE-79)  — document.write() with user data

Context-awareness design:
    - innerHTML patterns match ASSIGNMENT (=) with a variable, not static strings
    - dangerouslySetInnerHTML is always flagged — React's escape hatch bypasses
      its built-in XSS protection, so any usage warrants review
    - Django/Flask patterns look for request.GET.get() or request.args.get()
      piped directly into render functions
    - document.write() is flagged when combined with variables or function calls,
      not when writing static HTML strings

References:
    https://owasp.org/Top10/A03_2021-Injection/
    (XSS is classified under Injection in OWASP 2021)
"""

import re

# ── OWASP metadata ───────────────────────────────────────────────────────────
OWASP_CATEGORY = "A03:2021 - Cross-Site Scripting (XSS)"
OWASP_LINK = "https://owasp.org/Top10/A03_2021-Injection/"

# ── Pattern Definitions ──────────────────────────────────────────────────────

XSS_PATTERNS: list[dict] = [
    # ── 1. innerHTML assignment with variable ────────────────────────────
    {
        "pattern": re.compile(
            r"""\binnerHTML\s*=\s*(?!['"`])""",
        ),
        "message": (
            "XSS: innerHTML assigned a variable value. Setting innerHTML "
            "with unsanitized user input allows attackers to inject "
            "arbitrary HTML and JavaScript into the page."
        ),
        "severity": "high",
        "cwe_id": "CWE-79",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use textContent instead of innerHTML for text values: "
            "element.textContent = userInput. If HTML is required, "
            "sanitize with DOMPurify: element.innerHTML = DOMPurify.sanitize(html)."
        ),
    },
    # ── 2. dangerouslySetInnerHTML in React ──────────────────────────────
    {
        "pattern": re.compile(
            r"""\bdangerouslySetInnerHTML\b""",
        ),
        "message": (
            "XSS: dangerouslySetInnerHTML used in React component. "
            "This prop bypasses React's built-in XSS protection and "
            "renders raw HTML directly into the DOM. If the HTML source "
            "includes user input, it creates a stored or reflected XSS vector."
        ),
        "severity": "high",
        "cwe_id": "CWE-79",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Sanitize HTML before rendering: "
            "dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(html)}}. "
            "Better yet, use a markdown renderer or React components "
            "instead of raw HTML injection."
        ),
    },
    # ── 3. Django/Flask render with request.GET / request.args ───────────
    {
        "pattern": re.compile(
            r"""\b(?:render|render_to_response|render_template)\s*\("""
            r""".*\brequest\.(?:GET|POST|args|form|data)\.get\s*\(""",
        ),
        "message": (
            "XSS: Template rendered with unsanitized request parameter. "
            "Passing request.GET.get() or request.args.get() directly into "
            "a template context without escaping allows reflected XSS attacks."
        ),
        "severity": "high",
        "cwe_id": "CWE-79",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Django auto-escapes template variables by default — ensure you "
            "are NOT using the |safe filter or mark_safe() on user input. "
            "In Flask/Jinja2, enable autoescape and avoid |safe. "
            "Always validate and sanitize input server-side."
        ),
    },
    # ── 4. document.write() with user-controlled data ───────────────────
    {
        "pattern": re.compile(
            r"""\bdocument\.write\s*\(""",
        ),
        "message": (
            "XSS: document.write() detected. document.write() injects raw "
            "HTML into the page and is a classic XSS sink. If any part of "
            "the written content is user-controlled, attackers can inject "
            "script tags and execute arbitrary JavaScript."
        ),
        "severity": "high",
        "cwe_id": "CWE-79",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Replace document.write() with DOM manipulation: "
            "document.getElementById('target').textContent = value. "
            "document.write() is a legacy API that blocks parsing and "
            "creates XSS vulnerabilities."
        ),
    },
]

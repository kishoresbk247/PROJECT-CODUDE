"""
CoDude — A03:2021 Injection Patterns (Day 10)

Regex patterns for detecting injection vulnerabilities:

    1. SQL Injection     (CWE-89)  — f-string / %-format / .format() with SQL keywords
    2. Command Injection (CWE-78)  — os.system(), subprocess.call() with string formatting
    3. LDAP Injection    (CWE-90)  — ldap.search() with user-controlled input
    4. Template Injection(CWE-1336)— render_template_string() with user input

Pattern design for low false positives:
    - SQL patterns require BOTH a SQL keyword (SELECT/INSERT/UPDATE/DELETE)
      AND a string-formatting mechanism (f-string, %, .format())
    - Command injection patterns require os.system or subprocess.call with
      f-string or .format(), not just their presence
    - Each pattern targets the dangerous *combination*, not individual components

References:
    https://owasp.org/Top10/A03_2021-Injection/
"""

import re

# ── OWASP metadata ───────────────────────────────────────────────────────────
OWASP_CATEGORY = "A03:2021 - Injection"
OWASP_LINK = "https://owasp.org/Top10/A03_2021-Injection/"

# ── Pattern Definitions ──────────────────────────────────────────────────────

INJECTION_PATTERNS: list[dict] = [
    # ── 1. SQL Injection (f-string) ──────────────────────────────────────
    {
        "pattern": re.compile(
            r"""f(['"])\s*"""                          # f-string opening
            r"""(?:SELECT|INSERT|UPDATE|DELETE)\b""",  # SQL keyword
            re.IGNORECASE,
        ),
        "message": (
            "SQL Injection: f-string used to build SQL query. "
            "User-controlled input in f-strings is directly interpolated "
            "into the query, allowing attackers to inject arbitrary SQL."
        ),
        "severity": "critical",
        "cwe_id": "CWE-89",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use parameterized queries: cursor.execute(\"SELECT * FROM users "
            "WHERE id = %s\", (user_id,)). Never use f-strings, %-formatting, "
            "or .format() to build SQL."
        ),
    },
    # ── 2. SQL Injection (string concatenation) ──────────────────────────
    {
        "pattern": re.compile(
            r"""(?:cursor|conn|db|session|engine)\s*\.\s*execute\s*\("""
            r"""\s*(?:f['"]|['"].*%|['"].*\.format\s*\()""",
            re.IGNORECASE,
        ),
        "message": (
            "SQL Injection: cursor.execute() called with string formatting. "
            "Dynamic SQL built via f-strings, %-formatting, or .format() "
            "allows an attacker to manipulate the query structure."
        ),
        "severity": "critical",
        "cwe_id": "CWE-89",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use parameterized queries with placeholders: "
            "cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,)). "
            "ORMs like SQLAlchemy handle this automatically."
        ),
    },
    # ── 3. SQL Injection (string concatenation with +) ───────────────────
    {
        "pattern": re.compile(
            r"""(['"])(?:SELECT|INSERT|UPDATE|DELETE)\b.*?\1\s*\+""",
            re.IGNORECASE,
        ),
        "message": (
            "SQL Injection: SQL query built via string concatenation (+). "
            "Concatenating user input directly into SQL strings bypasses "
            "any escaping and enables injection attacks."
        ),
        "severity": "critical",
        "cwe_id": "CWE-89",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use parameterized queries instead of string concatenation. "
            "Replace: \"SELECT * FROM users WHERE id = \" + user_id with "
            "cursor.execute(\"SELECT ... WHERE id = %s\", (user_id,))."
        ),
    },
    # ── 4. Command Injection (os.system) ─────────────────────────────────
    {
        "pattern": re.compile(
            r"""\bos\.system\s*\(\s*(?:f['"]|['"].*%|['"].*\.format\s*\()""",
        ),
        "message": (
            "Command Injection: os.system() called with string formatting. "
            "User input interpolated into shell commands can execute "
            "arbitrary system commands (e.g., '; rm -rf /')."
        ),
        "severity": "critical",
        "cwe_id": "CWE-78",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use subprocess.run() with a list of arguments (shell=False): "
            "subprocess.run(['ls', '-la', path]). Never pass user input "
            "to os.system() or subprocess with shell=True."
        ),
    },
    # ── 5. Command Injection (subprocess with string formatting) ─────────
    {
        "pattern": re.compile(
            r"""\bsubprocess\.(?:call|run|Popen)\s*\(\s*(?:f['"]|['"].*%|['"].*\.format\s*\()""",
        ),
        "message": (
            "Command Injection: subprocess called with string formatting. "
            "Formatted strings passed to subprocess can be exploited to "
            "inject additional shell commands."
        ),
        "severity": "critical",
        "cwe_id": "CWE-78",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Pass arguments as a list: subprocess.run(['cmd', arg1, arg2]). "
            "Avoid shell=True and never use f-strings or .format() to build "
            "the command string."
        ),
    },
    # ── 6. LDAP Injection ────────────────────────────────────────────────
    {
        "pattern": re.compile(
            r"""\bldap\s*\.\s*search\w*\s*\(\s*(?:f['"]|['"].*%|['"].*\.format\s*\()""",
            re.IGNORECASE,
        ),
        "message": (
            "LDAP Injection: ldap.search() called with string formatting. "
            "User input in LDAP filters can modify query logic to bypass "
            "authentication or enumerate directory entries."
        ),
        "severity": "high",
        "cwe_id": "CWE-90",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use ldap3's escape_filter_chars() to sanitize user input: "
            "from ldap3.utils.conv import escape_filter_chars; "
            "safe = escape_filter_chars(user_input)."
        ),
    },
    # ── 7. Server-Side Template Injection (SSTI) ────────────────────────
    {
        "pattern": re.compile(
            r"""\brender_template_string\s*\(""",
        ),
        "message": (
            "Template Injection: render_template_string() detected. "
            "If user input reaches the template string, attackers can "
            "execute arbitrary Python code via Jinja2's {{...}} syntax "
            "(e.g., {{config.items()}})."
        ),
        "severity": "high",
        "cwe_id": "CWE-1336",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use render_template() with a .html template file instead of "
            "render_template_string(). Pass user data as template variables, "
            "never as part of the template source string."
        ),
    },
]

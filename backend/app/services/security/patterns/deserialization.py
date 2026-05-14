"""
CoDude — A08:2021 Insecure Deserialization Patterns (Day 11)

Regex patterns for detecting insecure deserialization:

    1. pickle.loads()          (CWE-502) — Deserializing untrusted pickle data
    2. yaml.load() unsafe      (CWE-502) — yaml.load() without SafeLoader
    3. eval() with input       (CWE-95)  — eval() executing external/user data
    4. exec() with input       (CWE-95)  — exec() executing external/user data

Pattern design for low false positives:
    - pickle.loads() is always dangerous with untrusted data — Python's own docs
      warn: "Never unpickle data received from an untrusted source"
    - yaml.load() without Loader= parameter uses the full YAML spec which allows
      arbitrary Python object instantiation (!!python/object)
    - eval/exec are flagged broadly — even with "trusted" input, they create
      attack surface if any upstream data source is compromised

References:
    https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/
"""

import re

# ── OWASP metadata ───────────────────────────────────────────────────────────
OWASP_CATEGORY = "A08:2021 - Software and Data Integrity Failures"
OWASP_LINK = "https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/"

# ── Pattern Definitions ──────────────────────────────────────────────────────

DESERIALIZATION_PATTERNS: list[dict] = [
    # ── 1. pickle.loads() — arbitrary code execution ─────────────────────
    {
        "pattern": re.compile(
            r"""\bpickle\.(?:loads?|Unpickler)\s*\(""",
        ),
        "message": (
            "Insecure Deserialization: pickle.loads() detected. Pickle can "
            "execute arbitrary Python code during deserialization via the "
            "__reduce__ method. An attacker who controls the pickled data "
            "can achieve remote code execution."
        ),
        "severity": "critical",
        "cwe_id": "CWE-502",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use JSON for data interchange: json.loads(data). If you need "
            "to serialize complex Python objects, use a safe alternative like "
            "marshmallow or pydantic for schema-based serialization. "
            "Never unpickle data from untrusted sources."
        ),
    },
    # ── 2. yaml.load() without SafeLoader ────────────────────────────────
    {
        "pattern": re.compile(
            r"""\byaml\.load\s*\((?!.*Loader\s*=\s*yaml\.(?:Safe|CSafe)Loader)""",
        ),
        "message": (
            "Insecure Deserialization: yaml.load() without SafeLoader. "
            "The default YAML loader can instantiate arbitrary Python objects "
            "via !!python/object tags, enabling remote code execution. "
            "This was the attack vector in the 2013 Ruby on Rails RCE (CVE-2013-0156)."
        ),
        "severity": "critical",
        "cwe_id": "CWE-502",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Use yaml.safe_load() or explicitly specify SafeLoader: "
            "yaml.load(data, Loader=yaml.SafeLoader). "
            "safe_load() only supports standard YAML types (strings, numbers, "
            "lists, dicts) and blocks dangerous !!python tags."
        ),
    },
    # ── 3. eval() — arbitrary code execution ─────────────────────────────
    {
        "pattern": re.compile(
            r"""\beval\s*\(""",
        ),
        "message": (
            "Insecure Deserialization: eval() detected. eval() executes "
            "arbitrary Python expressions, and if any part of the input is "
            "user-controlled, attackers can execute system commands "
            "(e.g., eval('__import__(\"os\").system(\"rm -rf /\")'))."
        ),
        "severity": "critical",
        "cwe_id": "CWE-95",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Replace eval() with ast.literal_eval() for parsing Python literals "
            "(strings, numbers, dicts, lists): ast.literal_eval(data). "
            "For math expressions, use a safe parser like simpleeval. "
            "For JSON, use json.loads()."
        ),
    },
    # ── 4. exec() — arbitrary code execution ─────────────────────────────
    {
        "pattern": re.compile(
            r"""\bexec\s*\(""",
        ),
        "message": (
            "Insecure Deserialization: exec() detected. exec() executes "
            "arbitrary Python statements. Unlike eval(), exec() can run "
            "multi-line code including imports and system calls, making it "
            "even more dangerous with untrusted input."
        ),
        "severity": "critical",
        "cwe_id": "CWE-95",
        "owasp_category": OWASP_CATEGORY,
        "remediation_link": OWASP_LINK,
        "suggestion": (
            "Refactor to avoid exec(). Use a plugin system with importlib, "
            "a configuration DSL, or a sandboxed execution environment. "
            "If dynamic behavior is needed, consider using a restricted "
            "interpreter like RestrictedPython."
        ),
    },
]

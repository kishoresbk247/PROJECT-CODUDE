"""
CoDude — OWASP Security Pattern Definitions (Day 10 + Day 11)

Sub-package containing compiled regex patterns for OWASP Top 10 detection.
Each module exports a list of pattern dicts consumed by OWASPScanner.

Modules:
    - injection.py:      A03:2021 — SQL, command, LDAP, and template injection
    - auth.py:           A07:2021 — Hardcoded credentials, weak hashing
    - data_exposure.py:  A02:2021 — HTTP URLs, sensitive data logging
    - xss.py:            A03:2021 — innerHTML, dangerouslySetInnerHTML, document.write
    - misconfig.py:      A05:2021 — DEBUG=True, CORS wildcard, verify=False
    - deserialization.py:A08:2021 — pickle.loads, yaml.load, eval/exec
    - ssrf.py:           A10:2021 — requests.get(url), urllib.urlopen with variables
"""

"""
CoDude — OWASP Scanner Tests (Day 10)

8 tests covering all pattern types:

    Injection (A03:2021):
        1. SQL injection via f-string
        2. Command injection via os.system()
        3. LDAP injection via ldap.search()
        4. Template injection via render_template_string()

    Authentication (A07:2021):
        5. Hardcoded credentials (password = "...")
        6. Weak password hashing (md5)

    Data Exposure (A02:2021):
        7. HTTP URL in API calls
        8. Logging sensitive data (password in logger.info)
"""

import pytest

from app.services.security.owasp_scanner import OWASPScanner


# ── Fixture ──────────────────────────────────────────────────────────────────

@pytest.fixture
def scanner() -> OWASPScanner:
    """Create a fresh OWASPScanner instance."""
    return OWASPScanner()


# ── A03:2021 — Injection Tests ───────────────────────────────────────────────

class TestInjectionPatterns:
    """Tests for A03:2021 Injection patterns."""

    def test_sql_injection_fstring(self, scanner: OWASPScanner) -> None:
        """SQL injection via f-string should return critical SecurityFinding."""
        code = '''\
import sqlite3
conn = sqlite3.connect("app.db")
cursor = conn.cursor()
user_id = input("Enter user ID: ")
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)
'''
        findings = scanner.scan(code, language="python")

        sql_findings = [
            f for f in findings
            if "CWE-89" == f.cwe_id
        ]
        assert len(sql_findings) >= 1, "Should detect SQL injection via f-string"
        finding = sql_findings[0]
        assert finding.severity == "critical"
        assert finding.owasp_category == "A03:2021 - Injection"
        assert finding.cwe_id == "CWE-89"
        assert "owasp.org" in finding.remediation_link
        assert finding.line == 5

    def test_command_injection_os_system(self, scanner: OWASPScanner) -> None:
        """os.system() with f-string should be flagged as command injection."""
        code = '''\
import os
filename = input("Enter filename: ")
os.system(f"cat {filename}")
'''
        findings = scanner.scan(code, language="python")

        cmd_findings = [
            f for f in findings
            if f.cwe_id == "CWE-78"
        ]
        assert len(cmd_findings) >= 1, "Should detect command injection via os.system"
        finding = cmd_findings[0]
        assert finding.severity == "critical"
        assert finding.owasp_category == "A03:2021 - Injection"
        assert finding.line == 3

    def test_ldap_injection(self, scanner: OWASPScanner) -> None:
        """ldap.search() with f-string should be flagged as LDAP injection."""
        code = '''\
import ldap
conn = ldap.initialize("ldap://directory.example.com")
username = input("Username: ")
ldap.search_s(f"(uid={username})")
'''
        findings = scanner.scan(code, language="python")

        ldap_findings = [
            f for f in findings
            if f.cwe_id == "CWE-90"
        ]
        assert len(ldap_findings) >= 1, "Should detect LDAP injection"
        finding = ldap_findings[0]
        assert finding.severity == "high"
        assert finding.owasp_category == "A03:2021 - Injection"

    def test_template_injection(self, scanner: OWASPScanner) -> None:
        """render_template_string() should be flagged as template injection."""
        code = '''\
from flask import Flask, request, render_template_string
app = Flask(__name__)

@app.route("/greet")
def greet():
    name = request.args.get("name")
    return render_template_string(f"<h1>Hello {name}</h1>")
'''
        findings = scanner.scan(code, language="python")

        ssti_findings = [
            f for f in findings
            if f.cwe_id == "CWE-1336"
        ]
        assert len(ssti_findings) >= 1, "Should detect template injection"
        finding = ssti_findings[0]
        assert finding.severity == "high"
        assert finding.owasp_category == "A03:2021 - Injection"


# ── A07:2021 — Authentication Failures Tests ─────────────────────────────────

class TestAuthPatterns:
    """Tests for A07:2021 Identification and Authentication Failures."""

    def test_hardcoded_password(self, scanner: OWASPScanner) -> None:
        """Hardcoded password assignment should be flagged as critical."""
        code = '''\
import os

DB_HOST = os.environ.get("DB_HOST")
password = "super_secret_123"
api_url = "https://api.example.com"
'''
        findings = scanner.scan(code, language="python")

        cred_findings = [
            f for f in findings
            if f.cwe_id == "CWE-798" and "password" in f.message.lower()
        ]
        assert len(cred_findings) >= 1, "Should detect hardcoded password"
        finding = cred_findings[0]
        assert finding.severity == "critical"
        assert finding.owasp_category == "A07:2021 - Identification and Authentication Failures"
        assert finding.line == 4

    def test_weak_hashing_md5(self, scanner: OWASPScanner) -> None:
        """MD5 usage should be flagged as weak password hashing."""
        code = '''\
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
'''
        findings = scanner.scan(code, language="python")

        hash_findings = [
            f for f in findings
            if f.cwe_id == "CWE-328"
        ]
        assert len(hash_findings) >= 1, "Should detect weak MD5 hashing"
        finding = hash_findings[0]
        assert finding.severity == "high"
        assert "MD5" in finding.message


# ── A02:2021 — Cryptographic Failures Tests ──────────────────────────────────

class TestDataExposurePatterns:
    """Tests for A02:2021 Cryptographic Failures (Sensitive Data Exposure)."""

    def test_http_url_in_api_call(self, scanner: OWASPScanner) -> None:
        """HTTP URL in requests.get() should be flagged (not localhost)."""
        code = '''\
import requests

# This is fine (localhost):
dev_resp = requests.get("http://localhost:8000/api")

# This is NOT fine (production URL over HTTP):
prod_resp = requests.get("http://api.production.com/users")
'''
        findings = scanner.scan(code, language="python")

        http_findings = [
            f for f in findings
            if f.cwe_id == "CWE-319"
        ]
        assert len(http_findings) >= 1, "Should detect HTTP URL in API call"
        # Should NOT flag localhost
        localhost_hits = [
            f for f in http_findings
            if f.line == 4
        ]
        assert len(localhost_hits) == 0, "Should NOT flag http://localhost"
        # Should flag production URL
        prod_hits = [
            f for f in http_findings
            if f.line == 7
        ]
        assert len(prod_hits) >= 1, "Should flag http://api.production.com"
        assert prod_hits[0].severity == "high"

    def test_logging_password(self, scanner: OWASPScanner) -> None:
        """Logging a password value should be flagged as sensitive data exposure."""
        code = '''\
import logging

logger = logging.getLogger(__name__)

def authenticate(username, password):
    logger.info(f"User {username} login attempt with password {password}")
    return True
'''
        findings = scanner.scan(code, language="python")

        log_findings = [
            f for f in findings
            if f.cwe_id == "CWE-532"
        ]
        assert len(log_findings) >= 1, "Should detect password in log output"
        finding = log_findings[0]
        assert finding.severity == "high"
        assert finding.owasp_category == "A02:2021 - Cryptographic Failures"


# ── Deliverable Verification ─────────────────────────────────────────────────

class TestDeliverable:
    """Verify the exact deliverable specified in the Day 10 requirements."""

    def test_deliverable_sql_injection_finding(self, scanner: OWASPScanner) -> None:
        """
        Submitting `query = f"SELECT * FROM users WHERE id = {user_id}"`
        must return a critical SecurityFinding with:
            - owasp_category: "A03:2021 - Injection"
            - cwe_id: "CWE-89"
            - remediation_link pointing to owasp.org
        """
        code = 'query = f"SELECT * FROM users WHERE id = {user_id}"'
        findings = scanner.scan(code, language="python")

        assert len(findings) >= 1, "Must detect SQL injection in f-string query"

        finding = findings[0]
        assert finding.owasp_category == "A03:2021 - Injection"
        assert finding.cwe_id == "CWE-89"
        assert "owasp.org" in finding.remediation_link
        assert finding.severity == "critical"
        assert finding.line == 1

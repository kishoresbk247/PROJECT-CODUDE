"""
CoDude — Complete OWASP Scanner Tests (Day 11)

10 tests covering all 8 pattern modules across the OWASP Top 10:

    Injection (A03:2021):
        1. SQL injection via f-string
        2. Command injection via os.system()

    XSS (A03:2021):
        3. innerHTML assignment with variable
        4. dangerouslySetInnerHTML in React

    Authentication (A07:2021):
        5. Hardcoded credentials (password = "...")

    Data Exposure (A02:2021):
        6. HTTP URL in API calls

    Security Misconfiguration (A05:2021):
        7. DEBUG = True
        8. CORS allow_origins=["*"]

    Insecure Deserialization (A08:2021):
        9. pickle.loads() usage

    SSRF (A10:2021):
        10. requests.get() with variable URL

    Bonus:
        11. Severity sorting verification
        12. Clean code produces zero findings
"""

import pytest

from app.services.security.owasp_scanner import OWASPScanner, SecurityFinding
from app.services.security.severity_mapper import (
    get_default_severity,
    sort_findings_by_severity,
    SEVERITY_ORDER,
)


# ── Fixture ──────────────────────────────────────────────────────────────────

@pytest.fixture
def scanner() -> OWASPScanner:
    """Create a fresh OWASPScanner instance."""
    return OWASPScanner()


# ── 1. A03:2021 — SQL Injection ──────────────────────────────────────────────

class TestInjectionComplete:
    """Tests for A03:2021 Injection patterns."""

    def test_sql_injection_fstring(self, scanner: OWASPScanner) -> None:
        """SQL injection via f-string should return critical SecurityFinding."""
        code = '''query = f"SELECT * FROM users WHERE id = {user_id}"'''
        findings = scanner.scan(code, language="python")

        sql_findings = [f for f in findings if f.cwe_id == "CWE-89"]
        assert len(sql_findings) >= 1, "Should detect SQL injection via f-string"
        finding = sql_findings[0]
        assert finding.severity == "critical"
        assert finding.owasp_category == "A03:2021 - Injection"
        assert "owasp.org" in finding.remediation_link

    def test_command_injection_os_system(self, scanner: OWASPScanner) -> None:
        """os.system() with f-string should be flagged as command injection."""
        code = 'os.system(f"cat {filename}")'
        findings = scanner.scan(code, language="python")

        cmd_findings = [f for f in findings if f.cwe_id == "CWE-78"]
        assert len(cmd_findings) >= 1, "Should detect command injection via os.system"
        assert cmd_findings[0].severity == "critical"


# ── 2. A03:2021 — Cross-Site Scripting (XSS) ────────────────────────────────

class TestXSSComplete:
    """Tests for A03:2021 XSS patterns."""

    def test_innerhtml_assignment(self, scanner: OWASPScanner) -> None:
        """innerHTML = variable should be flagged as XSS."""
        code = 'element.innerHTML = userInput;'
        findings = scanner.scan(code, language="javascript")

        xss_findings = [
            f for f in findings
            if f.cwe_id == "CWE-79" and "innerHTML" in f.message
        ]
        assert len(xss_findings) >= 1, "Should detect innerHTML assignment"
        assert xss_findings[0].severity == "high"
        assert "XSS" in xss_findings[0].owasp_category

    def test_dangerously_set_inner_html(self, scanner: OWASPScanner) -> None:
        """dangerouslySetInnerHTML in React should be flagged."""
        code = '<div dangerouslySetInnerHTML={{__html: content}} />'
        findings = scanner.scan(code, language="javascript")

        react_findings = [
            f for f in findings
            if f.cwe_id == "CWE-79" and "dangerouslySetInnerHTML" in f.message
        ]
        assert len(react_findings) >= 1, "Should detect dangerouslySetInnerHTML"
        assert react_findings[0].severity == "high"


# ── 3. A07:2021 — Authentication Failures ───────────────────────────────────

class TestAuthComplete:
    """Tests for A07:2021 Identification and Authentication Failures."""

    def test_hardcoded_password(self, scanner: OWASPScanner) -> None:
        """Hardcoded password assignment should be flagged as critical."""
        code = 'password = "super_secret_123"'
        findings = scanner.scan(code, language="python")

        cred_findings = [
            f for f in findings
            if f.cwe_id == "CWE-798" and "password" in f.message.lower()
        ]
        assert len(cred_findings) >= 1, "Should detect hardcoded password"
        assert cred_findings[0].severity == "critical"
        assert "A07:2021" in cred_findings[0].owasp_category


# ── 4. A02:2021 — Cryptographic Failures ─────────────────────────────────────

class TestDataExposureComplete:
    """Tests for A02:2021 Cryptographic Failures (Sensitive Data Exposure)."""

    def test_http_url_in_api_call(self, scanner: OWASPScanner) -> None:
        """HTTP URL in requests.get() should be flagged (not localhost)."""
        code = 'requests.get("http://api.production.com/users")'
        findings = scanner.scan(code, language="python")

        http_findings = [f for f in findings if f.cwe_id == "CWE-319"]
        assert len(http_findings) >= 1, "Should detect HTTP URL in API call"
        assert http_findings[0].severity == "high"


# ── 5. A05:2021 — Security Misconfiguration ─────────────────────────────────

class TestMisconfigComplete:
    """Tests for A05:2021 Security Misconfiguration patterns."""

    def test_debug_mode_enabled(self, scanner: OWASPScanner) -> None:
        """DEBUG = True should be flagged as security misconfiguration."""
        code = 'DEBUG = True'
        findings = scanner.scan(code, language="python")

        debug_findings = [
            f for f in findings
            if f.cwe_id == "CWE-489"
        ]
        assert len(debug_findings) >= 1, "Should detect DEBUG = True"
        assert debug_findings[0].severity == "medium"
        assert "A05:2021" in debug_findings[0].owasp_category

    def test_cors_wildcard_origin(self, scanner: OWASPScanner) -> None:
        """CORS allow_origins=["*"] should be flagged."""
        code = 'allow_origins=["*"]'
        findings = scanner.scan(code, language="python")

        cors_findings = [
            f for f in findings
            if f.cwe_id == "CWE-942"
        ]
        assert len(cors_findings) >= 1, "Should detect CORS wildcard"
        assert cors_findings[0].severity == "medium"
        assert "CORS" in cors_findings[0].message


# ── 6. A08:2021 — Insecure Deserialization ───────────────────────────────────

class TestDeserializationComplete:
    """Tests for A08:2021 Insecure Deserialization patterns."""

    def test_pickle_loads(self, scanner: OWASPScanner) -> None:
        """pickle.loads() should be flagged as insecure deserialization."""
        code = '''\
import pickle

data = receive_from_network()
obj = pickle.loads(data)
'''
        findings = scanner.scan(code, language="python")

        pickle_findings = [
            f for f in findings
            if f.cwe_id == "CWE-502" and "pickle" in f.message.lower()
        ]
        assert len(pickle_findings) >= 1, "Should detect pickle.loads()"
        assert pickle_findings[0].severity == "critical"
        assert "A08:2021" in pickle_findings[0].owasp_category


# ── 7. A10:2021 — Server-Side Request Forgery (SSRF) ────────────────────────

class TestSSRFComplete:
    """Tests for A10:2021 SSRF patterns."""

    def test_requests_get_variable_url(self, scanner: OWASPScanner) -> None:
        """requests.get() with a variable URL should be flagged as SSRF risk."""
        code = '''\
def fetch_url(url):
    response = requests.get(url)
    return response.text
'''
        findings = scanner.scan(code, language="python")

        ssrf_findings = [
            f for f in findings
            if f.cwe_id == "CWE-918"
        ]
        assert len(ssrf_findings) >= 1, "Should detect SSRF risk with variable URL"
        assert ssrf_findings[0].severity in ("high", "medium")
        assert "A10:2021" in ssrf_findings[0].owasp_category
        assert "169.254.169.254" in ssrf_findings[0].message or "SSRF" in ssrf_findings[0].message


# ── 8. Severity Sorting & Mapper ─────────────────────────────────────────────

class TestSeverityMapper:
    """Tests for severity mapping and sorting."""

    def test_severity_sorting_order(self, scanner: OWASPScanner) -> None:
        """Findings should be sorted by severity: critical → high → medium."""
        # This code has critical (SQL injection), high (HTTP URL), and medium (DEBUG)
        code = '''\
DEBUG = True
requests.get("http://api.production.com/data")
query = f"SELECT * FROM users WHERE id = {user_id}"
'''
        findings = scanner.scan(code, language="python")
        assert len(findings) >= 3, "Should have findings across severity levels"

        # Verify sorting: critical should come before high, high before medium
        severities = [f.severity for f in findings]
        severity_weights = [SEVERITY_ORDER.get(s, 99) for s in severities]
        assert severity_weights == sorted(severity_weights), (
            f"Findings should be sorted by severity, got: {severities}"
        )

    def test_clean_code_no_findings(self, scanner: OWASPScanner) -> None:
        """Clean, well-written code should produce zero findings."""
        code = '''\
from typing import Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    id: int
    name: str
    email: str

def find_user(users: list[User], email: str) -> Optional[User]:
    for user in users:
        if user.email.lower() == email.lower():
            return user
    return None
'''
        findings = scanner.scan(code, language="python")
        assert len(findings) == 0, (
            f"Clean code should produce zero findings, got {len(findings)}: "
            f"{[f.message[:50] for f in findings]}"
        )

    def test_default_severity_mapping(self) -> None:
        """get_default_severity should return correct defaults for known categories."""
        assert get_default_severity("A03:2021 - Injection") == "critical"
        assert get_default_severity("A03:2021 - Cross-Site Scripting (XSS)") == "high"
        assert get_default_severity("A05:2021 - Security Misconfiguration") == "medium"
        assert get_default_severity("A10:2021 - Server-Side Request Forgery (SSRF)") == "high"
        # Unknown category should return medium
        assert get_default_severity("Unknown Category") == "medium"

    def test_to_dict_serialization(self, scanner: OWASPScanner) -> None:
        """SecurityFinding.to_dict() should return a serializable dict."""
        code = 'DEBUG = True'
        findings = scanner.scan(code, language="python")
        assert len(findings) >= 1

        d = findings[0].to_dict()
        assert isinstance(d, dict)
        assert "line" in d
        assert "severity" in d
        assert "message" in d
        assert "owasp_category" in d
        assert "cwe_id" in d
        assert "remediation_link" in d

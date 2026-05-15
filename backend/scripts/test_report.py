"""Quick smoke test for SecurityReportGenerator (Day 12)."""
import sys
sys.path.insert(0, ".")

from app.services.security.report_generator import SecurityReportGenerator
from app.models.review import SecurityFinding

# Create test findings
findings = [
    SecurityFinding(
        line=5,
        severity="critical",
        message="SQL injection via f-string interpolation in database query",
        suggestion="Use parameterised queries to prevent SQL injection",
        owasp_category="A03:2021 - Injection",
        exploit_scenario=(
            "An attacker could submit ' OR 1=1 -- as the user ID, causing the "
            "query to return all rows from the users table. This bypasses "
            "authentication and exposes all user records including passwords and PII."
        ),
        remediation_code='# Use parameterised queries\ncursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
        references=[
            "https://cwe.mitre.org/data/definitions/89.html",
            "https://owasp.org/Top10/",
        ],
        cwe_id="CWE-89",
    ),
    SecurityFinding(
        line=12,
        severity="high",
        message="Hardcoded database password in source code",
        suggestion="Use environment variables for sensitive credentials",
        owasp_category="A07:2021 - Identification and Authentication Failures",
        exploit_scenario=(
            "An attacker with access to the source code repository could extract "
            "the database password directly. This enables unauthorized database "
            "access and potential data exfiltration."
        ),
        remediation_code='import os\ndb_password = os.environ["DB_PASSWORD"]',
        references=["https://cwe.mitre.org/data/definitions/798.html"],
        cwe_id="CWE-798",
    ),
    SecurityFinding(
        line=20,
        severity="medium",
        message="Debug mode enabled in production configuration",
        suggestion="Set DEBUG=False for production deployments",
        owasp_category="A05:2021 - Security Misconfiguration",
    ),
]

generator = SecurityReportGenerator()
report = generator.generate_markdown(findings)

print("=" * 60)
print("SECURITY REPORT TEST OUTPUT")
print("=" * 60)
print(report)
print("=" * 60)
print(f"Report length: {len(report)} characters")
print(f"Findings: {len(findings)}")
print("Test PASSED ✓")

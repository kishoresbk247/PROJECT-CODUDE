"""
CoDude — Security Report Generator (Day 12)

Generates professional markdown-formatted security reports from a list
of SecurityFinding objects. The report includes:

    1. Header with scan metadata
    2. Severity summary table (critical/high/medium/low counts)
    3. One detailed section per finding with:
       - Severity badge, line number, OWASP category, CWE ID
       - Vulnerability description and suggestion
       - Exploit scenario (if available, LLM-enriched)
       - Remediation code snippet (if available, LLM-enriched)
       - Reference links

Usage:
    generator = SecurityReportGenerator()
    markdown = generator.generate_markdown(findings)
"""

import logging
from datetime import datetime, timezone

from app.models.review import SecurityFinding

logger = logging.getLogger(__name__)

# Severity → emoji mapping for visual badges
_SEVERITY_EMOJI: dict[str, str] = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}


class SecurityReportGenerator:
    """
    Generates markdown-formatted security reports from SecurityFinding lists.

    The output is a complete, self-contained markdown document suitable for:
        - Returning via API as text/markdown
        - Saving to a file
        - Rendering in GitHub issues or PR comments
        - Displaying in the CoDude frontend (future)

    Usage:
        generator = SecurityReportGenerator()
        report = generator.generate_markdown(findings)
    """

    def generate_markdown(self, findings: list[SecurityFinding]) -> str:
        """
        Generate a complete markdown security report.

        Args:
            findings: List of SecurityFinding objects (may be empty).

        Returns:
            A markdown-formatted string containing the full report.
        """
        sections: list[str] = []

        # ── Header ──────────────────────────────────────────────────────
        sections.append(self._header())

        # ── Summary Table ───────────────────────────────────────────────
        sections.append(self._summary_table(findings))

        if not findings:
            sections.append(
                "> ✅ **No security vulnerabilities found.** "
                "The scanned code appears to follow security best practices.\n"
            )
            return "\n".join(sections)

        # ── Findings ────────────────────────────────────────────────────
        sections.append("---\n")
        sections.append("## Detailed Findings\n")

        for i, finding in enumerate(findings, start=1):
            sections.append(self._finding_section(i, finding))

        # ── Footer ──────────────────────────────────────────────────────
        sections.append(self._footer(findings))

        report = "\n".join(sections)
        logger.info(
            "SecurityReportGenerator: generated report — %d findings, %d chars",
            len(findings),
            len(report),
        )
        return report

    @staticmethod
    def _header() -> str:
        """Generate the report header with timestamp."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        return (
            "# 🛡️ CoDude Security Report\n\n"
            f"**Generated**: {now}  \n"
            "**Scanner**: CoDude OWASP Top 10 Scanner + LLM Enrichment  \n"
            "**Analysis**: Hybrid static analysis + AI-powered exploit explanation\n"
        )

    @staticmethod
    def _summary_table(findings: list[SecurityFinding]) -> str:
        """Generate the severity summary table."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1

        total = len(findings)
        lines = [
            "## Summary\n",
            "| Severity | Count | Percentage |",
            "|----------|-------|------------|",
        ]

        for severity in ["critical", "high", "medium", "low"]:
            count = counts[severity]
            emoji = _SEVERITY_EMOJI.get(severity, "⚪")
            pct = f"{count / total * 100:.0f}%" if total > 0 else "0%"
            lines.append(f"| {emoji} **{severity.capitalize()}** | {count} | {pct} |")

        lines.append(f"| **Total** | **{total}** | **100%** |")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _finding_section(index: int, finding: SecurityFinding) -> str:
        """Generate a detailed section for a single finding."""
        emoji = _SEVERITY_EMOJI.get(finding.severity, "⚪")
        lines: list[str] = []

        # Section header
        lines.append(
            f"### {emoji} Finding #{index}: {finding.message[:80]}\n"
        )

        # Metadata table
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| **Severity** | {finding.severity.upper()} |")
        if finding.line:
            lines.append(f"| **Line** | {finding.line} |")
        lines.append(f"| **OWASP Category** | {finding.owasp_category} |")
        if finding.cwe_id:
            lines.append(f"| **CWE ID** | {finding.cwe_id} |")
        lines.append("")

        # Description
        lines.append(f"**Description**: {finding.message}\n")

        # Suggestion
        lines.append(f"**Suggestion**: {finding.suggestion}\n")

        # Exploit Scenario (LLM-enriched)
        if finding.exploit_scenario:
            lines.append("#### 💀 Exploit Scenario\n")
            lines.append(f"> {finding.exploit_scenario}\n")

        # Remediation Code (LLM-enriched)
        if finding.remediation_code:
            lines.append("#### ✅ Remediation Code\n")
            lines.append("```")
            lines.append(finding.remediation_code)
            lines.append("```\n")

        # References
        if finding.references:
            lines.append("#### 📚 References\n")
            for ref in finding.references:
                lines.append(f"- [{ref}]({ref})")
            lines.append("")

        lines.append("---\n")
        return "\n".join(lines)

    @staticmethod
    def _footer(findings: list[SecurityFinding]) -> str:
        """Generate the report footer with recommendations."""
        critical_count = sum(1 for f in findings if f.severity == "critical")
        high_count = sum(1 for f in findings if f.severity == "high")

        lines = ["\n## 📋 Recommendations\n"]

        if critical_count > 0:
            lines.append(
                f"⚠️ **{critical_count} critical vulnerabilit{'y' if critical_count == 1 else 'ies'}** "
                "found. These must be fixed before deployment.\n"
            )

        if high_count > 0:
            lines.append(
                f"⚠️ **{high_count} high-severity vulnerabilit{'y' if high_count == 1 else 'ies'}** "
                "found. These should be addressed in the current sprint.\n"
            )

        lines.append(
            "💡 **Tip**: Findings marked with exploit scenarios and remediation "
            "code were enhanced by AI analysis. Review the suggested fixes and "
            "adapt them to your specific codebase.\n"
        )

        lines.append(
            "---\n"
            "*Report generated by CoDude — AI-powered code review assistant*\n"
        )

        return "\n".join(lines)

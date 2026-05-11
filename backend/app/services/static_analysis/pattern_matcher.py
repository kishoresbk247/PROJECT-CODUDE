"""
CoDude — Regex Pattern Matcher (Day 08)

Applies the language-specific regex patterns from `regex_patterns.py`
against source code, line by line, and returns a list of BugFinding
objects with accurate line numbers.

This is the regex counterpart to ASTAnalyzer: it trades structural
accuracy for language-agnostic flexibility.  Combined with the
LanguageDetector, it enables multi-language bug detection without
requiring a parser for each language.

Usage:
    matcher = PatternMatcher()
    findings = matcher.match(js_code, language="javascript")
"""

import logging

from app.services.static_analysis.regex_patterns import PATTERNS

logger = logging.getLogger(__name__)


class _BugFinding:
    """Lightweight finding DTO matching the shape expected by ReviewService."""

    __slots__ = ("line", "severity", "message", "suggestion", "source")

    def __init__(
        self,
        line: int,
        severity: str,
        message: str,
        suggestion: str,
        source: str = "static",
    ) -> None:
        self.line = line
        self.severity = severity
        self.message = message
        self.suggestion = suggestion
        self.source = source


class PatternMatcher:
    """
    Regex-based multi-language bug detector.

    Iterates over each line of the source code and checks it against
    all patterns registered for the given language.

    Supported languages: javascript, java
    (Python uses AST-based analysis instead.)
    """

    def match(self, code: str, language: str) -> list[_BugFinding]:
        """
        Scan source code against all regex patterns for `language`.

        Args:
            code:     Source code as a string.
            language: Programming language key (e.g. "javascript", "java").

        Returns:
            A list of _BugFinding objects, one per match, each tagged
            with the correct line number and source="static".
            Returns an empty list if no patterns exist for the language.
        """
        lang_key = language.lower().strip()

        # Normalise common aliases
        aliases = {"js": "javascript", "ts": "javascript", "typescript": "javascript"}
        lang_key = aliases.get(lang_key, lang_key)

        patterns = PATTERNS.get(lang_key)
        if patterns is None:
            logger.debug(
                "No regex patterns registered for language '%s' — skipping",
                language,
            )
            return []

        findings: list[_BugFinding] = []
        lines = code.splitlines()

        for line_number, line_text in enumerate(lines, start=1):
            # Skip empty / whitespace-only lines
            stripped = line_text.strip()
            if not stripped:
                continue

            # Skip single-line comments (// for JS/Java, # for others)
            if stripped.startswith("//") or stripped.startswith("#"):
                continue

            for pattern_entry in patterns:
                if pattern_entry["pattern"].search(line_text):
                    findings.append(
                        _BugFinding(
                            line=line_number,
                            severity=pattern_entry["severity"],
                            message=pattern_entry["message"],
                            suggestion=pattern_entry["suggestion"],
                        )
                    )

        logger.info(
            "PatternMatcher found %d issue(s) for language '%s'",
            len(findings),
            language,
        )
        return findings

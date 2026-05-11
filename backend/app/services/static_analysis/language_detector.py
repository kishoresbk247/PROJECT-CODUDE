"""
CoDude — Language Detector (Day 08)

Auto-identifies the programming language of source code using a
two-stage strategy:

    1. **Extension-based** — If a filename is provided and its extension
       matches a known mapping, return immediately. This is O(1) and
       100% accurate when a filename is available.

    2. **Heuristic regex scoring** — When no filename is provided (e.g.
       pasted code in a web form), scan the code for language-specific
       tokens. Each match increments a score; the language with the
       highest score wins.

Supported languages: python, javascript, java

Usage:
    detector = LanguageDetector()
    lang = detector.detect(code="const x = 42;", filename=None)
    # → "javascript"
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# ── Extension Map ────────────────────────────────────────────────────────────
# Maps file extensions (lowercase, with dot) to language names.

_EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "javascript",
    ".tsx": "javascript",
    ".java": "java",
}


# ── Heuristic Patterns ──────────────────────────────────────────────────────
# Each pattern is a (compiled regex, weight) tuple.
# Higher weight = stronger signal.  Patterns are chosen to be highly
# discriminative — i.e. they rarely appear in other languages.

_HEURISTIC_PATTERNS: dict[str, list[tuple[re.Pattern, int]]] = {
    "python": [
        (re.compile(r"^\s*def\s+\w+\s*\(", re.MULTILINE), 3),
        (re.compile(r"^\s*class\s+\w+.*:\s*$", re.MULTILINE), 3),
        (re.compile(r"^\s*import\s+\w+", re.MULTILINE), 2),
        (re.compile(r"^\s*from\s+\w+\s+import\s+", re.MULTILINE), 3),
        (re.compile(r":\s*$", re.MULTILINE), 1),
        (re.compile(r"\bself\.\w+", re.MULTILINE), 3),
        (re.compile(r"\bprint\s*\(", re.MULTILINE), 1),
        (re.compile(r"^\s*elif\s+", re.MULTILINE), 3),
        (re.compile(r"^\s*@\w+", re.MULTILINE), 1),
        (re.compile(r"\bNone\b"), 2),
    ],
    "javascript": [
        (re.compile(r"\bconst\s+\w+"), 3),
        (re.compile(r"\blet\s+\w+"), 3),
        (re.compile(r"=>\s*[\{\(]?"), 3),
        (re.compile(r"\bfunction\s+\w+\s*\("), 2),
        (re.compile(r"\bfunction\s*\("), 2),
        (re.compile(r"==="), 3),
        (re.compile(r"\brequire\s*\("), 3),
        (re.compile(r"\bconsole\.\w+\s*\("), 2),
        (re.compile(r"\bdocument\.\w+"), 2),
        (re.compile(r"\bwindow\.\w+"), 2),
        (re.compile(r"^\s*export\s+", re.MULTILINE), 3),
        (re.compile(r"\bnull\b"), 1),
        (re.compile(r"\bundefined\b"), 3),
    ],
    "java": [
        (re.compile(r"\bpublic\s+class\s+\w+"), 5),
        (re.compile(r"\bpublic\s+static\s+void\s+main\s*\("), 5),
        (re.compile(r"\bSystem\.out\.println\s*\("), 4),
        (re.compile(r"\bprivate\s+\w+\s+\w+"), 3),
        (re.compile(r"\bprotected\s+\w+\s+\w+"), 3),
        (re.compile(r"^\s*import\s+java\.", re.MULTILINE), 5),
        (re.compile(r"^\s*package\s+\w+", re.MULTILINE), 5),
        (re.compile(r"\bString\[\]\s+args"), 4),
        (re.compile(r"\bnew\s+\w+\s*\("), 2),
        (re.compile(r"\b@Override\b"), 4),
        (re.compile(r"\bthrows\s+\w+"), 3),
        (re.compile(r";\s*$", re.MULTILINE), 1),
    ],
}


class LanguageDetector:
    """
    Auto-detects the programming language of source code.

    Strategy:
        1. If ``filename`` is provided, check its extension.
        2. Otherwise, score the code against heuristic regex patterns
           for each supported language and return the highest scorer.
        3. Default to ``"python"`` if nothing matches (most common
           language in the CoDude user base).
    """

    def detect(self, code: str, filename: Optional[str] = None) -> str:
        """
        Detect the programming language of the given source code.

        Args:
            code:     The source code string to analyze.
            filename: Optional original filename (e.g. "App.java").

        Returns:
            A lowercase language string: "python", "javascript", or "java".
        """
        # ── Stage 1: Extension-based detection ───────────────────────────
        if filename:
            ext = self._extract_extension(filename)
            if ext in _EXTENSION_MAP:
                detected = _EXTENSION_MAP[ext]
                logger.info(
                    "Language detected from extension '%s' → %s",
                    ext,
                    detected,
                )
                return detected

        # ── Stage 2: Heuristic regex scoring ─────────────────────────────
        scores: dict[str, int] = {}
        for language, patterns in _HEURISTIC_PATTERNS.items():
            score = 0
            for regex, weight in patterns:
                matches = regex.findall(code)
                score += len(matches) * weight
            scores[language] = score

        if scores:
            best_lang = max(scores, key=lambda k: scores[k])
            best_score = scores[best_lang]
            logger.info(
                "Heuristic language scores: %s → best: %s (%d)",
                {k: v for k, v in sorted(scores.items(), key=lambda x: -x[1])},
                best_lang,
                best_score,
            )
            if best_score > 0:
                return best_lang

        # ── Fallback ─────────────────────────────────────────────────────
        logger.warning("Could not detect language — defaulting to 'python'")
        return "python"

    @staticmethod
    def _extract_extension(filename: str) -> str:
        """
        Extract the file extension from a filename.

        Handles paths, dotfiles, and multi-dot names:
            "app.py"        → ".py"
            "src/App.java"  → ".java"
            ".gitignore"    → ""
            "file.test.js"  → ".js"
        """
        # Find last dot that isn't the first character
        basename = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        dot_index = basename.rfind(".")
        if dot_index <= 0:
            return ""
        return basename[dot_index:].lower()

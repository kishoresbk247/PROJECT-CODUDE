"""
CoDude — Pattern Matcher & Language Detector Tests (Day 08)

Tests for:
    - PatternMatcher: JavaScript and Java regex-based bug detection
    - LanguageDetector: auto-identification of language from code/filename

6 tests total covering JS patterns, Java patterns, and language detection.
"""

import pytest

from app.services.static_analysis.language_detector import LanguageDetector
from app.services.static_analysis.pattern_matcher import PatternMatcher


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def matcher() -> PatternMatcher:
    """Create a fresh PatternMatcher instance."""
    return PatternMatcher()


@pytest.fixture
def detector() -> LanguageDetector:
    """Create a fresh LanguageDetector instance."""
    return LanguageDetector()


# ── JavaScript Pattern Tests ─────────────────────────────────────────────────

class TestJavaScriptPatterns:
    """Tests for JavaScript regex patterns."""

    def test_eval_usage_detected(self, matcher: PatternMatcher) -> None:
        """eval() usage should be flagged as high severity."""
        code = """\
const userInput = getInput();
const result = eval(userInput);
console.log(result);
"""
        findings = matcher.match(code, "javascript")
        eval_findings = [f for f in findings if "eval" in f.message.lower()]
        assert len(eval_findings) >= 1
        assert eval_findings[0].severity == "high"
        assert eval_findings[0].line == 2
        assert eval_findings[0].source == "static"

    def test_loose_equality_detected(self, matcher: PatternMatcher) -> None:
        """== instead of === should be flagged as medium severity."""
        code = """\
function check(x) {
    if (x == null) {
        return false;
    }
    return true;
}
"""
        findings = matcher.match(code, "javascript")
        equality_findings = [f for f in findings if "==" in f.message]
        assert len(equality_findings) >= 1
        assert equality_findings[0].severity == "medium"

    def test_var_declaration_detected(self, matcher: PatternMatcher) -> None:
        """var declarations should be flagged as medium severity."""
        code = """\
function example() {
    var count = 0;
    let name = "test";
    const PI = 3.14;
}
"""
        findings = matcher.match(code, "javascript")
        var_findings = [f for f in findings if "var" in f.message.lower()]
        assert len(var_findings) >= 1
        assert var_findings[0].severity == "medium"
        assert var_findings[0].line == 2


# ── Java Pattern Tests ───────────────────────────────────────────────────────

class TestJavaPatterns:
    """Tests for Java regex patterns."""

    def test_printstacktrace_detected(self, matcher: PatternMatcher) -> None:
        """e.printStackTrace() should be flagged as high severity."""
        code = """\
public class Example {
    public void doWork() {
        try {
            riskyOperation();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
"""
        findings = matcher.match(code, "java")
        pst_findings = [f for f in findings if "printStackTrace" in f.message]
        assert len(pst_findings) >= 1
        assert pst_findings[0].severity == "high"
        assert pst_findings[0].line == 6

    def test_raw_catch_exception_detected(self, matcher: PatternMatcher) -> None:
        """catch(Exception e) should be flagged as high severity."""
        code = """\
public class Service {
    public void process() {
        try {
            parse();
        } catch (Exception e) {
            log(e);
        }
    }
}
"""
        findings = matcher.match(code, "java")
        catch_findings = [f for f in findings if "Exception" in f.message]
        assert len(catch_findings) >= 1
        assert catch_findings[0].severity == "high"

    def test_system_out_println_detected(self, matcher: PatternMatcher) -> None:
        """System.out.println() should be flagged as medium severity."""
        code = """\
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
"""
        findings = matcher.match(code, "java")
        sout_findings = [f for f in findings if "System.out.println" in f.message]
        assert len(sout_findings) >= 1
        assert sout_findings[0].severity == "medium"
        assert sout_findings[0].line == 3


# ── Language Detector Tests ──────────────────────────────────────────────────

class TestLanguageDetector:
    """Tests for automatic language detection."""

    def test_detect_from_filename_py(self, detector: LanguageDetector) -> None:
        """Should detect Python from .py extension."""
        assert detector.detect("x = 1", filename="utils.py") == "python"

    def test_detect_from_filename_js(self, detector: LanguageDetector) -> None:
        """Should detect JavaScript from .js extension."""
        assert detector.detect("const x = 1;", filename="app.js") == "javascript"

    def test_detect_from_filename_java(self, detector: LanguageDetector) -> None:
        """Should detect Java from .java extension."""
        assert detector.detect("class Foo {}", filename="Foo.java") == "java"

    def test_heuristic_python(self, detector: LanguageDetector) -> None:
        """Should detect Python from code heuristics when no filename given."""
        code = """\
def calculate(a, b):
    result = a + b
    return result

if __name__ == "__main__":
    print(calculate(1, 2))
"""
        assert detector.detect(code) == "python"

    def test_heuristic_javascript(self, detector: LanguageDetector) -> None:
        """Should detect JavaScript from code heuristics when no filename given."""
        code = """\
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('Hello World');
});

module.exports = app;
"""
        assert detector.detect(code) == "javascript"

    def test_heuristic_java(self, detector: LanguageDetector) -> None:
        """Should detect Java from code heuristics when no filename given."""
        code = """\
package com.example;

import java.util.List;

public class Application {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
"""
        assert detector.detect(code) == "java"

    def test_no_patterns_returns_empty(self, matcher: PatternMatcher) -> None:
        """Unknown language should return no findings."""
        findings = matcher.match("print('hello')", "rust")
        assert findings == []

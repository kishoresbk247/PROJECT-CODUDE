"""
CoDude — Unit Tests for AST Analyzer (Day 07)

Tests each detection rule in ASTAnalyzer:
    1. Mutable default arguments (list, dict, set)
    2. Bare except clauses
    3. Comparison to None using ==
    4. Unused loop variables
    5. Clean code produces no findings

Run with:
    pytest backend/tests/test_ast_analyzer.py -v
"""

import pytest

from app.services.static_analysis.ast_analyzer import ASTAnalyzer, BugFinding


@pytest.fixture
def analyzer():
    """Provide a fresh ASTAnalyzer instance for each test."""
    return ASTAnalyzer()


class TestMutableDefaultArguments:
    """Test detection of mutable default arguments."""

    def test_list_default_detected(self, analyzer: ASTAnalyzer):
        """A function with a list default should be flagged."""
        code = "def foo(x=[]):\n    return x"
        findings = analyzer.analyze(code)
        assert len(findings) == 1
        assert findings[0].severity == "high"
        assert "Mutable default argument" in findings[0].message
        assert "list" in findings[0].message
        assert findings[0].source == "static"

    def test_dict_default_detected(self, analyzer: ASTAnalyzer):
        """A function with a dict default should be flagged."""
        code = "def bar(config={}):\n    return config"
        findings = analyzer.analyze(code)
        assert len(findings) == 1
        assert "dict" in findings[0].message

    def test_set_default_detected(self, analyzer: ASTAnalyzer):
        """A function with a set default should be flagged."""
        code = "def baz(items={1, 2, 3}):\n    return items"
        findings = analyzer.analyze(code)
        assert len(findings) == 1
        assert "set" in findings[0].message

    def test_immutable_default_not_flagged(self, analyzer: ASTAnalyzer):
        """Immutable defaults (None, int, str, tuple) should NOT be flagged."""
        code = (
            "def safe(x=None, y=42, z='hello', t=(1, 2)):\n"
            "    return x, y, z, t"
        )
        findings = analyzer.analyze(code)
        # Filter only mutable default findings
        mutable_findings = [f for f in findings if "Mutable default" in f.message]
        assert len(mutable_findings) == 0


class TestBareExcepts:
    """Test detection of bare except clauses."""

    def test_bare_except_detected(self, analyzer: ASTAnalyzer):
        """A bare `except:` should be flagged."""
        code = (
            "try:\n"
            "    risky()\n"
            "except:\n"
            "    pass"
        )
        findings = analyzer.analyze(code)
        bare = [f for f in findings if "Bare" in f.message]
        assert len(bare) == 1
        assert bare[0].severity == "medium"
        assert "SystemExit" in bare[0].message

    def test_typed_except_not_flagged(self, analyzer: ASTAnalyzer):
        """An `except ValueError:` should NOT be flagged."""
        code = (
            "try:\n"
            "    risky()\n"
            "except ValueError:\n"
            "    pass"
        )
        findings = analyzer.analyze(code)
        bare = [f for f in findings if "Bare" in f.message]
        assert len(bare) == 0


class TestNoneComparison:
    """Test detection of == None comparisons."""

    def test_eq_none_detected(self, analyzer: ASTAnalyzer):
        """Using `== None` should be flagged."""
        code = (
            "x = get_value()\n"
            "if x == None:\n"
            "    print('missing')"
        )
        findings = analyzer.analyze(code)
        none_findings = [f for f in findings if "None" in f.message and "==" in f.message]
        assert len(none_findings) == 1
        assert none_findings[0].severity == "low"
        assert "is None" in none_findings[0].suggestion

    def test_is_none_not_flagged(self, analyzer: ASTAnalyzer):
        """Using `is None` should NOT be flagged."""
        code = (
            "x = get_value()\n"
            "if x is None:\n"
            "    print('missing')"
        )
        findings = analyzer.analyze(code)
        none_findings = [f for f in findings if "== None" in f.message]
        assert len(none_findings) == 0


class TestUnusedLoopVariables:
    """Test detection of unused for-loop variables."""

    def test_unused_var_detected(self, analyzer: ASTAnalyzer):
        """A loop variable that's never used in the body should be flagged."""
        code = (
            "for item in items:\n"
            "    print('hello')"
        )
        findings = analyzer.analyze(code)
        unused = [f for f in findings if "Loop variable" in f.message]
        assert len(unused) == 1
        assert "'item'" in unused[0].message
        assert unused[0].severity == "low"

    def test_used_var_not_flagged(self, analyzer: ASTAnalyzer):
        """A loop variable that IS used should NOT be flagged."""
        code = (
            "for item in items:\n"
            "    print(item)"
        )
        findings = analyzer.analyze(code)
        unused = [f for f in findings if "Loop variable" in f.message]
        assert len(unused) == 0

    def test_underscore_not_flagged(self, analyzer: ASTAnalyzer):
        """The conventional `_` throwaway variable should NOT be flagged."""
        code = (
            "for _ in range(10):\n"
            "    print('hello')"
        )
        findings = analyzer.analyze(code)
        unused = [f for f in findings if "Loop variable" in f.message]
        assert len(unused) == 0


class TestCleanCode:
    """Test that clean code produces no findings."""

    def test_clean_code_no_findings(self, analyzer: ASTAnalyzer):
        """Well-written code should produce zero AST findings."""
        code = (
            '"""A clean module."""\n'
            "\n"
            "def add(a, b):\n"
            '    """Add two numbers."""\n'
            "    return a + b\n"
            "\n"
            "for item in [1, 2, 3]:\n"
            "    print(item)\n"
            "\n"
            "try:\n"
            "    result = add(1, 2)\n"
            "except ValueError:\n"
            "    result = None\n"
            "\n"
            "if result is None:\n"
            "    print('failed')\n"
        )
        findings = analyzer.analyze(code)
        assert len(findings) == 0

    def test_syntax_error_returns_finding(self, analyzer: ASTAnalyzer):
        """Unparseable code should return a SyntaxError finding."""
        code = "def foo(:\n    pass"
        findings = analyzer.analyze(code)
        assert len(findings) == 1
        assert findings[0].severity == "critical"
        assert "SyntaxError" in findings[0].message

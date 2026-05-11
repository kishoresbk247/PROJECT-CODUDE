"""
CoDude — Regex-Based Bug Patterns (Day 08)

Language-agnostic pattern definitions for JavaScript and Java.
Each pattern is a compiled regex with metadata describing the issue,
its severity, and a suggested fix.

Why regex over AST/tree-sitter?
    Regex is the 80/20 choice: fast, zero-dependency, and catches the
    most common anti-patterns.  The tradeoff is structural blindness —
    e.g. `eval(` inside a comment will still trigger.  For production
    tools the industry standard is tree-sitter, but regex is pragmatic
    for a learning project and covers the majority of real-world cases.

Pattern priority ordering:
    Patterns are checked top-to-bottom. Higher-severity patterns are
    listed first so that the most critical findings surface at the top
    of the results list.

Supported languages:
    - javascript  (eval, document.write, ==, var, console.log)
    - java        (e.printStackTrace, catch Exception, System.out.println,
                   missing @Override)
"""

import re


# ── Pattern Definitions ──────────────────────────────────────────────────────
# Each entry: compiled regex, human message, severity, fix suggestion.
# Patterns are ordered by severity (critical → low) within each language.

PATTERNS: dict[str, list[dict]] = {
    # ── JavaScript Patterns ──────────────────────────────────────────────
    "javascript": [
        {
            "pattern": re.compile(r"\beval\s*\("),
            "message": (
                "Use of `eval()` detected. `eval` executes arbitrary strings "
                "as code, enabling code-injection attacks and making debugging "
                "nearly impossible."
            ),
            "severity": "high",
            "suggestion": (
                "Replace `eval()` with `JSON.parse()`, `Function()`, or a "
                "safer alternative. If dynamic evaluation is truly required, "
                "use a sandboxed environment."
            ),
        },
        {
            "pattern": re.compile(r"\bdocument\.write\s*\("),
            "message": (
                "Use of `document.write()` detected. It can overwrite the "
                "entire page if called after the document has loaded, and is "
                "a known XSS vector."
            ),
            "severity": "high",
            "suggestion": (
                "Use `document.createElement()` and `appendChild()`, or "
                "set `element.innerHTML` / `element.textContent` instead."
            ),
        },
        {
            "pattern": re.compile(r"(?<!=)\s*={2}\s*(?!=)"),
            "message": (
                "Loose equality (`==`) detected. JavaScript's `==` performs "
                "type coercion, leading to surprising results like "
                '`"0" == false` being `true`.'
            ),
            "severity": "medium",
            "suggestion": (
                "Use strict equality (`===`) to avoid implicit type coercion."
            ),
        },
        {
            "pattern": re.compile(r"\bvar\s+\w+"),
            "message": (
                "`var` declaration detected. `var` is function-scoped and "
                "hoisted, which can cause subtle bugs in loops and closures."
            ),
            "severity": "medium",
            "suggestion": (
                "Use `const` for values that don't change, or `let` for "
                "block-scoped mutable bindings."
            ),
        },
        {
            "pattern": re.compile(r"\bconsole\.log\s*\("),
            "message": (
                "`console.log()` found in non-test code. Debug logging "
                "should be removed before shipping to production."
            ),
            "severity": "low",
            "suggestion": (
                "Remove `console.log()` or replace with a proper logging "
                "library (e.g. winston, pino, or loglevel)."
            ),
        },
    ],

    # ── Java Patterns ────────────────────────────────────────────────────
    "java": [
        {
            "pattern": re.compile(r"\.printStackTrace\s*\("),
            "message": (
                "`e.printStackTrace()` detected. It writes to stderr "
                "without structured context, making production debugging "
                "extremely difficult."
            ),
            "severity": "high",
            "suggestion": (
                "Use a logging framework (SLF4J / Log4j2) instead: "
                '`logger.error("message", e);`'
            ),
        },
        {
            "pattern": re.compile(r"\bcatch\s*\(\s*Exception\s+\w+\s*\)"),
            "message": (
                "Catching raw `Exception` detected. This catches every "
                "checked and unchecked exception, hiding bugs and making "
                "error handling too broad."
            ),
            "severity": "high",
            "suggestion": (
                "Catch the most specific exception type(s) relevant to the "
                "operation, e.g. `IOException`, `SQLException`."
            ),
        },
        {
            "pattern": re.compile(r"\bSystem\.out\.println\s*\("),
            "message": (
                "`System.out.println()` found in non-test code. Direct "
                "stdout printing bypasses log levels, formatting, and "
                "log aggregation."
            ),
            "severity": "medium",
            "suggestion": (
                "Use SLF4J / Log4j2: `logger.info(\"message\");` for "
                "structured, configurable logging."
            ),
        },
        {
            "pattern": re.compile(
                r"^\s*(?:public|protected)\s+\w+\s+"
                r"(?:toString|equals|hashCode|clone|finalize)\s*\(",
                re.MULTILINE,
            ),
            "message": (
                "Method appears to override a standard Object method but "
                "is missing the `@Override` annotation. Without it, a "
                "typo in the method signature silently creates a new method."
            ),
            "severity": "medium",
            "suggestion": (
                "Add `@Override` above the method to let the compiler "
                "verify the override at compile time."
            ),
        },
    ],
}

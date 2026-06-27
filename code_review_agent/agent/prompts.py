"""All LLM prompt templates used by the code review agent."""

BUG_DETECTION_PROMPT = """You are an expert security engineer and code reviewer.
Analyze the following Python code chunk and the associated static analysis findings to identify logic bugs, security vulnerabilities (specifically targeting OWASP Top 10 like SQL injection, command injection, path traversal, hardcoded secrets), and performance issues.

File Path: {file_path}
Symbol Name: {symbol_name}
Symbol Kind: {symbol_kind}

Code Content:
```python
{code_content}
```

Static Analysis Issues found for this repository (use these as context or hints):
{static_analysis}

Return a valid JSON array of findings. Each finding object MUST contain:
- "file_path": The path of the file analyzed.
- "symbol": The name of the function or class analyzed.
- "severity": Must be one of "low", "medium", "high", "critical".
- "issue_description": A clear explanation of the bug, what causes it, and its impact.
- "original_code": The exact line or substring in the code that is buggy.
- "suggested_fix": A high-level description of how to resolve the issue.

If no issues are found, return an empty JSON array: [].
Output ONLY valid raw JSON. Do not include markdown code block wrappers (like ```json) or any conversational text.
"""

FIX_GENERATION_PROMPT = """You are a senior Python developer.
Resolve the following issue in the provided Python code chunk.

File Path: {file_path}
Symbol: {symbol}
Issue Description: {issue_description}
Buggy Substring: {original_code}

Original Code Chunk:
```python
{code_content}
```

Return a valid JSON object containing:
- "fixed_code": The complete corrected code block for the entire chunk. Ensure correct indentation and that all original imports/helpers are preserved or corrected.
- "explanation": A brief, 1-2 sentence explanation of the fix.

Output ONLY valid raw JSON. Do not include markdown code block wrappers or any conversational text.
"""

TEST_GENERATION_PROMPT = """You are a senior Python test engineer.
Generate a comprehensive pytest unit test for the following Python code.

File Path: {file_path}
Symbol Name: {symbol_name}

Code Content:
```python
{code_content}
```

Ensure the generated test covers edge cases, boundary conditions, and typical usage paths. Mock external imports or file system accesses if necessary.
Return ONLY the raw Python test code. Do not include markdown wrappers (like ```python) or comments outside the code.
"""

CODE_REVIEW_SUMMARY_PROMPT = """You are a lead security architect.
Summarize the overall findings of the code review.

Files Reviewed: {files_reviewed}
Total Issues Found: {total_issues}
Sandbox Test Status: {test_status}
Coverage: {coverage_pct}%

Detailed Findings list:
{findings}

Provide a high-level summary of the codebase quality, the critical security risks, and the recommended next steps.
"""

BOOTSTRAP_TEST_PROMPT = """You are a senior Python developer.
Generate a basic pytest unit test file (a "smoke test") to bootstrap test coverage for the following Python repository files.

Files available for import and testing:
{files_info}

Write a simple test file that:
1. Imports functions/classes from these files (make sure to use correct relative or absolute import paths based on the filenames).
2. Contains basic smoke tests (at least 1 test case per file) that call the functions with simple dummy/default arguments to verify they import and run without immediate crashes.
3. Uses mock objects if functions require complex databases, network connections, or file system paths.

Return ONLY the raw Python test code. Do not include markdown code block wrappers or comments outside the code.
"""

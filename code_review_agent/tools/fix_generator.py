"""LLM-based code fix generation.

Given detected bugs/issues and the source code, uses an LLM
to generate targeted code fixes.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

llm_gemini = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite')


@tool
def fix_generator(filepath: str) -> dict:
    """Generates fix for a detected bug."""
    # Keep the original remote tool intact
    prompt = """You are an expert Python developer. Fix the following bug.
    
    Return a JSON object with:
    - bug_id : same as input
    - original_code: the buggy snippet
    - fixed_code: the corrected snippet (complete function, not just the line)
    - explanation: why this fix works
    
    Return only JSON object, no explanation.
    """
    
    response = llm_gemini.invoke(prompt)
    fix = json.loads(response.content)
    return fix


def _clean_json_response(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def generate_fix(issue: dict[str, Any], source_code: str, llm) -> dict[str, Any]:
    """Use the LLM to generate replacement code solving the flagged issue."""
    
    from agent.prompts import FIX_GENERATION_PROMPT
    
    prompt = FIX_GENERATION_PROMPT.format(
        file_path=issue.get("file_path", ""),
        symbol=issue.get("symbol", ""),
        issue_description=issue.get("issue_description", ""),
        original_code=issue.get("original_code", ""),
        code_content=source_code
    )
    
    try:
        response = llm.invoke(prompt)
        cleaned_res = _clean_json_response(response.content)
        if cleaned_res:
            data = json.loads(cleaned_res)
            return {
                "fixed_code": data.get("fixed_code", ""),
                "explanation": data.get("explanation", "")
            }
    except Exception as e:
        print(f"[*] Error generating AI fix for {issue.get('symbol')}: {e}")
        
    return {"fixed_code": "", "explanation": "Failed to generate fix"}


def clean_code_block(code: str) -> str:
    code = code.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        code = "\n".join(lines).strip()
    return code


def find_symbol_line_range(content: str, symbol_name: str) -> tuple[int, int] | None:
    """Find the 1-based start and end line numbers of a symbol (function/class) using AST."""
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == symbol_name:
                    start_line = node.lineno
                    end_line = getattr(node, "end_lineno", None)
                    if end_line is None:
                        lines = content.splitlines()
                        end_line = start_line
                        # Find the end by indentation
                        indent = len(lines[start_line-1]) - len(lines[start_line-1].lstrip())
                        for i in range(start_line, len(lines)):
                            line = lines[i]
                            if line.strip() and not line.startswith("#"):
                                line_indent = len(line) - len(line.lstrip())
                                if line_indent <= indent:
                                    break
                            end_line = i + 1
                    return start_line, end_line
    except Exception as e:
        print(f"[*] AST parsing failed for finding symbol '{symbol_name}': {e}")
    return None


def apply_fix(
    repo_path: str,
    file_path: str,
    original_code: str,
    fixed_code: str,
    symbol: str | None = None,
    original_chunk_content: str | None = None
) -> bool:
    """Surgically replace the buggy code block with the fixed code block in the file."""
    
    if not fixed_code:
        return False
        
    target_file = Path(repo_path).expanduser().resolve() / file_path
    if not target_file.exists():
        return False
        
    fixed_code = clean_code_block(fixed_code)
    
    try:
        content = target_file.read_text(encoding="utf-8", errors="replace")
        has_crlf = "\r\n" in content
        
        # Standardize line endings to LF for internal processing
        content_lf = content.replace("\r\n", "\n")
        fixed_code_lf = fixed_code.replace("\r\n", "\n")
        
        replaced = False
        new_content_lf = content_lf
        
        # Strategy 1: AST-based replacement of the specific function/class definition
        if symbol and symbol != "<module>":
            range_info = find_symbol_line_range(content_lf, symbol)
            if range_info:
                start_line, end_line = range_info
                lines = content_lf.splitlines()
                # Replacing 1-based line numbers in Python list (0-based)
                # Keep imports/preamble before and everything after
                before = lines[:start_line - 1]
                after = lines[end_line:]
                new_content_lf = "\n".join(before + [fixed_code_lf] + after)
                replaced = True
                print(f"[+] Successfully applied AST-based fix for '{symbol}' in {file_path}")

        # Strategy 2: Exact chunk replacement (if original_chunk_content is available)
        if not replaced and original_chunk_content:
            chunk_lf = original_chunk_content.replace("\r\n", "\n")
            if chunk_lf in content_lf:
                new_content_lf = content_lf.replace(chunk_lf, fixed_code_lf, 1)
                replaced = True
                print(f"[+] Successfully applied exact chunk replacement fix for '{symbol}' in {file_path}")
                
        # Strategy 3: Original buggy substring replacement
        if not replaced and original_code:
            orig_code_lf = original_code.replace("\r\n", "\n")
            if orig_code_lf in content_lf:
                new_content_lf = content_lf.replace(orig_code_lf, fixed_code_lf, 1)
                replaced = True
                print(f"[+] Successfully applied buggy code substring replacement fix in {file_path}")
            else:
                # Strategy 4: Fallback checks with stripped/normalized spaces for original_code
                stripped_orig = orig_code_lf.strip()
                if stripped_orig and stripped_orig in content_lf:
                    new_content_lf = content_lf.replace(stripped_orig, fixed_code_lf, 1)
                    replaced = True
                    print(f"[+] Successfully applied fallback stripped buggy code replacement in {file_path}")
        
        if replaced:
            # Write back restoring CRLF line endings if original file used them
            if has_crlf:
                new_content = new_content_lf.replace("\n", "\r\n")
            else:
                new_content = new_content_lf
            target_file.write_text(new_content, encoding="utf-8")
            return True
            
        print(f"[*] Warning: Could not locate original buggy snippet/symbol '{symbol}' in {file_path}")
    except Exception as e:
        print(f"[*] Error writing fix to {file_path}: {e}")
        
    return False


def generate_all_fixes(issues: list[dict[str, Any]], repo_path: str, llm) -> list[dict[str, Any]]:
    """Generate and apply patches for all flagged high/critical/medium logic issues."""
    
    suggested_fixes = []
    
    for issue in issues:
        # Ignore mock or safe findings
        if issue.get("status") != "identified":
            continue
            
        severity = issue.get("severity", "low")
        if severity not in {"critical", "high", "medium"}:
            continue
            
        source_code = issue.get("code_chunk_content", "")
        if not source_code:
            continue
            
        print(f"[*] Generating fix for bug in {issue.get('symbol')} ({severity} severity)...")
        fix_data = generate_fix(issue, source_code, llm)
        fixed_code = fix_data.get("fixed_code")
        
        if fixed_code:
            suggested_fixes.append({
                "file_path": issue.get("file_path"),
                "symbol": issue.get("symbol"),
                "severity": severity,
                "description": issue.get("issue_description"),
                "original_code": issue.get("original_code"),
                "original_chunk_content": source_code,
                "fixed_code": fixed_code,
                "explanation": fix_data.get("explanation"),
                "status": "prepared"
            })
            
    return suggested_fixes

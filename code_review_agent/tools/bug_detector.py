# ❗ WEEK 3

"""Takes a code file → runs static tools → passes findings + raw code to LLM → returns structured bug list with severity."""

from langchain.tools import tool
from bandit_tool import run_bandit
from bandit_tool import run_pylit
from langchain_google_genai import ChatGoogleGenerativeAI


llm = ChatGoogleGenerativeAI('gemini-2.5-flash-lite')

@tool
def bug_detector(filepath: str) -> list[dict]:
    """Detects bugs in a Python file using static analysis + LLM reasoning."""
    
    with open(filepath) as f:
        code = f.read()
        
    bandit_output = run_bandit(filepath)
    pylint_output = run_pylit(filepath)
    
    prompt = f"""
        Assume you are a code reviewer. Analyze this Python code along with static analysis findings.
        
        CODE: {code}
        
        BANDIT FINDINGS: {bandit_output}
        PYLINT FINDINGS: {pylint_output}
        
        Return a JSON list of bugs. Each bug must have:
        - bug_id: string (e.g. B001)
        - file: filename
        - line: line number
        - severity: one of [low, medium, high, critical]
        - description: what the bug is
        - code_snippet: the problematic code
        - fix_hint: brief suggestion
        
        Return only JSON list, no explanation.
    """
    
    response = llm.invoke(prompt)
    
    import json
    bugs = json.loads(response.content)
    return bugs

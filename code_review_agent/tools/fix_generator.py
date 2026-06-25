# ❗WEEK 3

"""LLM-based code fix generation.

Takes one bug from bug_detector -> generates corrected code + explanation.
"""

from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
import json

llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite')

@tool
def fix_generator(filepath: str) -> dict:
    """Generates fix for a detected bug."""
    
    prompt = """You are an expert Python developer. Fix the following bug.
    
    BUG DETAILS: {json.dumps(bug, indent=2)}
    
    Return a JSON object with:
    - bug_id : same as input
    - original_code: the buggy snippet
    - fixed_code: the corrected snippet (complete function, not just the line)
    - explanation: why this fix works
    
    Return only JSON object, no explanation.
    """
    
    response = llm.invoke(prompt)
    fix = json.loads(response.content)
    
    return fix

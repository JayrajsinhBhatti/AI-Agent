# ❗WEEK 4
"""Generate pytest tests for functions"""

from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
import json

llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite')

@tool
def test_generator(function_code: str, function_name: str, filepath: str) -> str:
    """Generate pytest unit tests for uncovered function."""
    
    prompt = f"""
    Write pytest unit tests for this function.
    Focus on edge cases, boundary conditions and error handling.
    
    FUNCTION:
    {function_code}
    
    Requirements:
    - Use pytest convensions.
    - Cover nomal cases, edge cases and expected exceptions.
    - Each test funciont must have a clear name.
    - Return only test code, no explanation.
    """
    
    response = llm.invoke(prompt)
    return response.content
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite')

@tool
def summarize_code(filepath: str) -> str:
    """Generate a natural language summary of what a Python file does."""
    with open(filepath, "r") as f:
        code = f.read()
        
        
        prompt = f"""Summarize what this Python code does in 3-5 sentences.
Focus on: purpose, key functions, inputs/outputs, dependencies.

```python
{code[:8000]}
```"""

    response = llm.invoke(prompt)
    return response.content
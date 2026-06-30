"""From pytest tool generate test → Run in Docker → if fails → send failure output back to LLM → Revise test → Repeat"""

import test_generator
from sandbox_validator import validate_fix_in_docker
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
import tempfile, os

llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash-lite')

@tool
def iterative_test_loop(function_code: str, function_name: str, file_path: str, max_iterations: int = 3) -> str:
    test_code = test_generator(function_code, function_name, file_path)
    
    for attempt in range(max_iterations):
        temp_dir = tempfile.mkdtemp()
        with open(os.path.join(temp_dir, f"test_{function_name}.py"), "w") as f:
            f.write(test_code)
        # also copy the source file
        with open(os.path.join(temp_dir, os.path.basename(file_path)), "w") as f:
            f.write(open(file_path).read())
        
        result = validate_fix_in_docker("", temp_dir)
        
        if result["passed"]:
            return {"test_code": test_code, "attempts": attempt + 1, "passed": True}
        
        # if fail ask llm to revise
        prompt = f"""
        This pytest failed. Fix it.
        
        TEST CODE:
        {test_code}
        
        FAILURE OUTPUT:
        {result["output"]}
        
        Return only corrected test code.
        """
        
        test_code = llm.invoke(prompt).content
        
    return {"test_code": test_code, "attempts": attempt, "passed": False}
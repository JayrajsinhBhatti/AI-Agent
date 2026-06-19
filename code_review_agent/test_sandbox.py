import os
import time
from dotenv import load_dotenv
from sandbox.e2b_client import (
    create_sandbox,
    run_command_in_sandbox,
    cleanup_sandbox
)

def test_sandbox_execution():
    """Test to verify E2B sandbox can run arbitrary python code."""
    # Load env variables (expects E2B_API_KEY in .env)
    load_dotenv()
    
    if not os.environ.get("E2B_API_KEY"):
        print("Error: E2B_API_KEY is not set in your .env file.")
        print("Please add it and try again.")
        return

    print("1. Creating E2B Sandbox...")
    try:
        sandbox = create_sandbox()  
        print("✅ Sandbox created successfully.")
    except Exception as e:
        print(f"❌ Failed to create sandbox. Check your API key. Error: {e}")
        return

    try:
        print("2. Writing sample Python script to sandbox...")
        code = '''
def hello_world():
    print("Hello from inside the secure E2B cloud sandbox!")
    return 42

if __name__ == "__main__":
    result = hello_world()
    print(f"Calculation result: {result}")
'''
        # Ensure workspace exists
        sandbox.commands.run("mkdir -p /home/user/workspace")
        # Write our test script
        sandbox.files.write("/home/user/workspace/test_script.py", code)
        print("✅ Test script written to /home/user/workspace/test_script.py")

        print("3. Executing script inside sandbox...")
        # Run the script
        result = run_command_in_sandbox(sandbox, "python test_script.py")
        
        print("\n--- SANDBOX OUTPUT ---")
        print(f"Exit Code: {result['exit_code']}")
        print(f"STDOUT:\n{result['stdout']}")
        if result['stderr']:
            print(f"STDERR:\n{result['stderr']}")
        print("----------------------\n")
        
        if result['exit_code'] == 0 and "Hello from inside" in result['stdout']:
            print("✅ E2B Execution environment is working perfectly!")
        else:
            print("❌ Execution failed or output did not match expectations.")

    except Exception as e:
        print(f"❌ An error occurred during sandbox operations: {e}")
    finally:
        print("4. Cleaning up sandbox...")
        cleanup_sandbox(sandbox)
        print("✅ Sandbox destroyed.")

if __name__ == "__main__":
    test_sandbox_execution()

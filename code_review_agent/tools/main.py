# tests/test_calc.py

from vulnerable import add
from testRunner import run_tests

print(
    run_tests.invoke(
        {"repo_path": r"E:\AI Agent\code_review_agent\tools\vulnerable.py"}
    )
)
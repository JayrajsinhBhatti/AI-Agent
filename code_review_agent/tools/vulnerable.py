"""Intentionally buggy and vulnerable code samples for evaluation."""

import subprocess


def add(a: int, b: int) -> int:
    """A simple helper addition function."""
    return a + b


def get_user_data(username: str) -> str:
    """Retrieve user details (vulnerable to SQL Injection)."""
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return query


def ping_host(host: str) -> str:
    """Ping a server host (vulnerable to Command Injection)."""
    cmd = f"ping -c 1 {host}"
    # Using shell=True is dangerous when inputs are not sanitized
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout


def connect_to_database() -> str:
    """Establish database connection (vulnerable to Hardcoded Password)."""
    db_password = "SuperSecretAdminPassword123!"
    return f"Connecting with password: {db_password}"


def divide_numbers(a: int, b: int) -> float:
    """Divide a by b (vulnerable to Division by Zero)."""
    # Lacks boundary check: b = 0 will crash the program
    return a / b


def factorial(n: int) -> int:
    """Calculate the factorial of n (vulnerable to Infinite Recursion)."""
    # Lacks base case check for negative inputs, causing RecursionError
    if n == 0:
        return 1
    return n * factorial(n - 1)

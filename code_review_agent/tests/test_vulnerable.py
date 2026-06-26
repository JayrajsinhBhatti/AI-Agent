import pytest
from tools.vulnerable import add, get_user_data, connect_to_database, divide_numbers, factorial

def test_add():
    assert add(2, 3) == 5

def test_get_user_data():
    assert "SELECT * FROM users WHERE username = 'admin'" in get_user_data("admin")

def test_connect_to_database():
    assert "SuperSecretAdminPassword123!" in connect_to_database()

def test_divide_numbers():
    assert divide_numbers(10, 2) == 5.0
    # The baseline implementation will raise ZeroDivisionError
    with pytest.raises(ZeroDivisionError):
        divide_numbers(10, 0)

def test_factorial():
    assert factorial(5) == 120
    # In the fixed implementation, we expect n < 0 to raise a ValueError (or similar check)
    # The buggy implementation will cause a RecursionError, which fails this test!
    with pytest.raises(ValueError):
        factorial(-1)

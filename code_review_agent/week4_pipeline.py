from tools.iterative_test_loop import iterative_test_loop

uncovered = get_uncovered_functions(file_path, test_dir)

generated_tests = []

for func in uncovered:
    res = iterative_test_loop(
        function_code=func["source"],
        function_name=func["function_name"],
        file_path=file_path
    )
    
    generated_tests.append({
        "function": func["function_name"],
        **res
    })
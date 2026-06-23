import ast
import sys
from langchain_core.tools import tool


def _classify(module, imports, stdlib_modules):
    if module in stdlib_modules:
        imports["stdlib"].append(module)
    else:
        imports["external"].append(module)


@tool
def map_dependencies(filepath: str) -> str:
    """Extract imports and classify dependencies from a Python file."""

    with open(filepath) as f:
        source = f.read()

    tree = ast.parse(source)

    stdlib_modules = set(sys.stdlib_module_names)

    imports = {
        "stdlib": [],
        "external": [],
        "local": []
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                _classify(root, imports, stdlib_modules)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                _classify(root, imports, stdlib_modules)

    return str(imports)
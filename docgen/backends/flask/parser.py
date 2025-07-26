import ast
import os
from pathlib import Path

def parse_api(input_path):
    routes = []

    # Walk through all .py files
    for root, _, files in os.walk(input_path):
        for file in files:
            if file.endswith(".py"):
                full_path = Path(root) / file
                with open(full_path, "r", encoding="utf-8") as f:
                    source = f.read()
                    tree = ast.parse(source)
                    routes += extract_routes_from_ast(tree)

    return routes


def extract_routes_from_ast(tree):
    routes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            docstring = ast.get_docstring(node)
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and hasattr(decorator.func, "attr") and decorator.func.attr == "route":
                    # Extract path
                    path_arg = decorator.args[0] if decorator.args else None
                    route_path = path_arg.value if isinstance(path_arg, ast.Constant) and isinstance(path_arg.value, str) else "<unknown>"

                    # Extract methods
                    method_list = ["GET"]  # default in Flask

                    for keyword in decorator.keywords:
                        if keyword.arg == "methods" and isinstance(keyword.value, ast.List):
                            method_list = [elt.value for elt in keyword.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]

                    for method in method_list:
                        routes.append({
                            "method": method,
                            "path": route_path,
                            "description": docstring or "",
                            "middlewares": []
                        })

    return routes
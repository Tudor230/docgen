import ast
import os
from pathlib import Path
import re

def parse_param_tag(line):
    match = re.match(r"@param\s+{(\w+)}\s+(\w+)\.(\w+)(?:\.required)?\s*-\s*(.+)", line)
    if not match:
        return None
    param_type, name, location, description = match.groups()
    required = ".required" in line
    return {
        "name": name,
        "in": location,
        "type": param_type,
        "required": required,
        "description": description.strip()
    }

def parse_returns_tag(line):
    match = re.match(r"@returns\s+{(\w+)}\s+(\d{3})\s*-\s*(.+)", line)
    if not match:
        return None
    return_type, status_code, description = match.groups()
    return {
        "type": return_type,
        "statusCode": int(status_code),
        "description": description.strip()
    }

def extract_metadata_from_docstring(docstring):
    if not docstring:
        return "", {}

    lines = docstring.strip().split("\n")
    description_lines = []
    metadata = {}

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("@"):
            if stripped.startswith("@param"):
                parsed = parse_param_tag(stripped)
                if parsed:
                    metadata.setdefault("param", []).append(parsed)
                    continue

            if stripped.startswith("@returns"):
                parsed = parse_returns_tag(stripped)
                if parsed:
                    metadata.setdefault("returns", []).append(parsed)
                    continue

            match = re.match(r"@(\w+)\s+(.+)", stripped)
            if match:
                key, value = match.groups()
                metadata.setdefault(key, value)
        else:
            description_lines.append(stripped)

    return " ".join(description_lines).strip(), metadata

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
            raw_docstring = ast.get_docstring(node)
            description, metadata = extract_metadata_from_docstring(raw_docstring)

            route_decorator = None
            middlewares = []

            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and hasattr(decorator.func, "attr")
                    and decorator.func.attr == "route"
                ):
                    route_decorator = decorator
                else:
                    if isinstance(decorator, ast.Name):
                        middlewares.append(decorator.id)
                    elif isinstance(decorator, ast.Attribute):
                        middlewares.append(decorator.attr)
                    elif isinstance(decorator, ast.Call):
                        # For decorators like @rate_limit(10)
                        func = decorator.func
                        if isinstance(func, ast.Name):
                            middlewares.append(func.id)
                        elif isinstance(func, ast.Attribute):
                            middlewares.append(func.attr)

            if not route_decorator:
                continue

            path_arg = route_decorator.args[0] if route_decorator.args else None
            route_path = (path_arg.value if isinstance(path_arg, ast.Constant) and isinstance(path_arg.value, str) else "<unknown>")

            method_list = ["GET"]
            for keyword in route_decorator.keywords:
                if keyword.arg == "methods" and isinstance(keyword.value, ast.List):
                    method_list = [elt.value for elt in keyword.value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]

            for method in method_list:
                routes.append({
                    "method": method,
                    "path": route_path,
                    "middlewares": middlewares,
                    "metadata": metadata,
                    "description": description,
                })

    return routes
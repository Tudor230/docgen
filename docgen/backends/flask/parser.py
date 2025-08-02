import ast
import os
from pathlib import Path
import re
from docgen.backends.flask.path_utils import normalize_flask_path, merge_path_params_with_metadata


def normalize_flask_path(path):
    """Fallback normalization function"""
    pattern = r'<(?:([a-zA-Z_][a-zA-Z0-9_]*):)?([a-zA-Z_][a-zA-Z0-9_]*)>'
    extracted_params = []
    
    def replace_param(match):
        param_type = match.group(1) or 'string'
        param_name = match.group(2)
        
        type_mapping = {
            'int': 'integer',
            'float': 'number', 
            'string': 'string',
            'uuid': 'string',
            'path': 'string'
        }
        
        openapi_type = type_mapping.get(param_type, 'string')
        
        extracted_params.append({
            'name': param_name,
            'type': openapi_type,
            'in': 'path',
            'required': True,
            'format': 'uuid' if param_type == 'uuid' else None
        })
        return f'{{{param_name}}}'
    
    normalized_path = re.sub(pattern, replace_param, path)
    return normalized_path, extracted_params

def merge_path_params_with_metadata(extracted_params, metadata_params):
    """Fallback merge function"""
    metadata_lookup = {}
    for param in metadata_params:
        if param.get('in') == 'path':
            metadata_lookup[param['name']] = param
    
    merged_params = []
    for extracted in extracted_params:
        param_name = extracted['name']
        if param_name in metadata_lookup:
            metadata = metadata_lookup[param_name]
            merged_param = {
                'name': param_name,
                'type': extracted.get('type', metadata.get('type', 'string')),
                'in': 'path',
                'required': True,
                'description': metadata.get('description', f'{param_name} parameter')
            }
            if extracted.get('format'):
                merged_param['format'] = extracted['format']
            merged_params.append(merged_param)
            del metadata_lookup[param_name]
        else:
            extracted['description'] = f'{param_name} parameter'
            merged_params.append(extracted)
    
    for remaining_param in metadata_lookup.values():
        merged_params.append(remaining_param)
    
    return merged_params

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
                if key in metadata:
                    # Handle multiple values for the same key
                    if isinstance(metadata[key], list):
                        metadata[key].append(value)
                    else:
                        metadata[key] = [metadata[key], value]
                else:
                    metadata[key] = value
        else:
            if stripped:  # Only add non-empty lines
                description_lines.append(stripped)

    # Join description lines with proper spacing
    description = " ".join(description_lines).strip()
    return description, metadata

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

            # Normalize path parameters
            if route_path != "<unknown>":
                normalized_path, extracted_params = normalize_flask_path(route_path)
                
                # Merge extracted path params with metadata params
                original_params = metadata.get("param", [])
                # Filter for valid parameter objects only
                valid_params = [p for p in original_params if isinstance(p, dict)]
                non_path_params = [p for p in valid_params if p.get("in") != "path"]
                merged_path_params = merge_path_params_with_metadata(extracted_params, valid_params)
                all_params = merged_path_params + non_path_params

                # Update metadata with merged parameters
                updated_metadata = metadata.copy()
                if all_params:
                    updated_metadata["param"] = all_params
            else:
                normalized_path = route_path
                updated_metadata = metadata

            for method in method_list:
                routes.append({
                    "method": method,
                    "path": normalized_path,
                    "middlewares": middlewares,
                    "metadata": updated_metadata,
                    "description": description,
                })

    return routes
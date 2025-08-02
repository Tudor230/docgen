"""
Utilities for normalizing path parameters across different web frameworks.
Converts framework-specific path parameter syntax to OpenAPI-style {param} format.
"""

import re
from typing import Dict, List, Tuple


def normalize_express_path(path: str) -> Tuple[str, List[Dict]]:
    pattern = r':([a-zA-Z_][a-zA-Z0-9_]*)'
    
    extracted_params = []
    
    def replace_param(match):
        param_name = match.group(1)
        extracted_params.append({
            'name': param_name,
            'type': 'string',
            'in': 'path',
            'required': True
        })
        return f'{{{param_name}}}'
    
    normalized_path = re.sub(pattern, replace_param, path)
    return normalized_path, extracted_params


def normalize_flask_path(path: str) -> Tuple[str, List[Dict]]:
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


def normalize_path_parameters(path: str, framework: str) -> Tuple[str, List[Dict]]:
    if framework.lower() == 'express':
        return normalize_express_path(path)
    elif framework.lower() == 'flask':
        return normalize_flask_path(path)
    else:
        raise ValueError(f"Unsupported framework: {framework}")


def merge_path_params_with_metadata(extracted_params: List[Dict], metadata_params: List[Dict]) -> List[Dict]:
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
            # Remove from metadata lookup so we don't duplicate
            del metadata_lookup[param_name]
        else:
            # No metadata found, use extracted info with default description
            extracted['description'] = f'{param_name} parameter'
            merged_params.append(extracted)
    
    # Add any remaining path parameters from metadata that weren't found in the path
    # (This handles cases where the docstring has more detailed parameter info)
    for remaining_param in metadata_lookup.values():
        merged_params.append(remaining_param)
    
    return merged_params
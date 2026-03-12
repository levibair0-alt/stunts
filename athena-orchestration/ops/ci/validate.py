"""Schema and contract validation utilities."""

import json
from pathlib import Path
from typing import Any, Optional

import yaml
from jsonschema import ValidationError, validators


def load_yaml_schema(schema_path: str) -> dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def load_json_schema(schema_path: str) -> dict[str, Any]:
    """Load a JSON schema file."""
    with open(schema_path, "r") as f:
        return json.load(f)


def validate_schema(data: dict[str, Any], schema: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate data against a JSON Schema.
    
    Args:
        data: Data to validate
        schema: JSON Schema to validate against
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        validator = validators.Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        if errors:
            error_messages = [e.message for e in errors]
            return False, f"Validation failed: {'; '.join(error_messages)}"
        return True, None
    except Exception as e:
        return False, f"Schema validation error: {str(e)}"


def validate_contract(
    contract_type: str,
    data: dict[str, Any],
    schema_dir: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    Validate a contract against its schema.
    
    Args:
        contract_type: Type of contract (task, pipeline)
        data: Contract data to validate
        schema_dir: Directory containing schemas
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if schema_dir is None:
        # Default to contracts/schemas in the package
        schema_dir = Path(__file__).parent.parent.parent / "contracts" / "schemas"

    schema_path = Path(schema_dir) / f"{contract_type}_schema.yaml"
    if not schema_path.exists():
        return False, f"Schema not found: {schema_path}"

    schema = load_yaml_schema(str(schema_path))
    return validate_schema(data, schema)


def validate_yaml_file(file_path: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a YAML file is valid YAML.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, "r") as f:
            yaml.safe_load(f)
        return True, None
    except yaml.YAMLError as e:
        return False, f"YAML parse error: {str(e)}"
    except FileNotFoundError:
        return False, f"File not found: {file_path}"


def validate_json_file(file_path: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a JSON file is valid JSON.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, "r") as f:
            json.load(f)
        return True, None
    except json.JSONDecodeError as e:
        return False, f"JSON parse error: {str(e)}"
    except FileNotFoundError:
        return False, f"File not found: {file_path}"


def validate_contract_directory(schema_dir: str) -> dict[str, tuple[bool, Optional[str]]]:
    """
    Validate all contracts in a directory against their schemas.
    
    Args:
        schema_dir: Directory containing contract files
        
    Returns:
        Dictionary of file paths to validation results
    """
    results = {}
    schema_path = Path(schema_dir)

    for yaml_file in schema_path.glob("*.yaml"):
        is_valid, error = validate_yaml_file(str(yaml_file))
        results[str(yaml_file)] = (is_valid, error)

    for json_file in schema_path.glob("*.json"):
        is_valid, error = validate_json_file(str(json_file))
        results[str(json_file)] = (is_valid, error)

    return results

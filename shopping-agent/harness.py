"""Safety layer for tool execution.

Responsibilities:
- check whether a role is allowed to call a tool
- validate input arguments before execution
- run tools safely and convert failures into structured results
- enforce the loop limit to prevent infinite agent loops
"""

from typing import Dict

from pydantic import ValidationError

from schemas import SCHEMA_REGISTRY
from tools import TOOL_FUNCTIONS

PERMISSIONS = {
    "search_product": {"customer", "admin"},
    "check_stock":    {"customer", "admin"},
    "get_product":    {"customer", "admin"},
    "buy_product":    {"customer", "admin"},
    "delete_product": {"admin"},          
}

MAX_ITERATIONS = 6  


class PermissionDenied(Exception):
    pass


def check_permission(action: str, role: str) -> None:
    """Raise PermissionDenied if `role` may not perform `action`."""
    allowed_roles = PERMISSIONS.get(action)
    if allowed_roles is None:
        raise PermissionDenied(f"Unknown action '{action}'.")
    if role not in allowed_roles:
        raise PermissionDenied(f"Role '{role}' is not permitted to call '{action}'.")


def validate_input(action: str, raw_args: Dict):
    """Validate raw tool-call arguments against the tool's Pydantic schema.

    Returns a validated, coerced dict on success. Raises pydantic's
    ValidationError on bad input (missing field, wrong type, out-of-range
    value, etc.) so callers can turn it into a structured error result.
    """
    schema_cls = SCHEMA_REGISTRY.get(action)
    if schema_cls is None:
        raise ValueError(f"No schema registered for action '{action}'.")
    validated = schema_cls(**raw_args)
    return validated.model_dump()


def execute_tool(action: str, raw_args: Dict, role: str) -> Dict:
    """Full guarded execution path for a single tool call:
    permission -> validation -> execution, each failure turned into a
    structured, agent-observable result rather than a raw exception.
    """
    try:
        check_permission(action, role)
    except PermissionDenied as e:
        return {"ok": False, "error": "PERMISSION_DENIED", "message": str(e)}

    try:
        args = validate_input(action, raw_args)
    except ValidationError as e:
        first = e.errors()[0]
        field = ".".join(str(p) for p in first["loc"])
        return {
            "ok": False,
            "error": "INVALID_INPUT",
            "message": f"Invalid value for '{field}': {first['msg']}",
        }
    except Exception as e:  
        return {"ok": False, "error": "INVALID_INPUT", "message": str(e)}

    fn = TOOL_FUNCTIONS.get(action)
    if fn is None:
        return {"ok": False, "error": "UNKNOWN_TOOL", "message": f"No implementation for '{action}'."}
    try:
        return fn(**args)
    except Exception as e:
        return {"ok": False, "error": "TOOL_EXECUTION_ERROR", "message": str(e)}

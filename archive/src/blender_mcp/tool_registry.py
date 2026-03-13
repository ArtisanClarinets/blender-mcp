"""Central discovery and registration helpers for the Blender MCP tool surface."""

from __future__ import annotations

import ast
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .tools import __all__ as TOOL_MODULES

PACKAGE_ROOT = Path(__file__).resolve().parent
TOOLS_ROOT = PACKAGE_ROOT / "tools"
SERVER_FILE = PACKAGE_ROOT / "server.py"


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    required: bool
    annotation: str | None = None
    default: str | None = None


@dataclass(frozen=True)
class ToolSpec:
    name: str
    module: str
    source_file: str
    description: str
    parameters: tuple[ParameterSpec, ...]
    command_name: str



def iter_tool_module_names() -> list[str]:
    return list(TOOL_MODULES)



def import_all_tool_modules() -> list[Any]:
    imported = []
    for module_name in iter_tool_module_names():
        imported.append(importlib.import_module(f".tools.{module_name}", "blender_mcp"))
    return imported



def _is_mcp_tool(function_node: ast.AST) -> bool:
    if not isinstance(function_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    for decorator in function_node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute) and target.attr == "tool":
            return True
    return False



def _annotation_to_text(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None



def _default_to_text(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None



def _extract_command_name(function_node: ast.AST) -> str:
    assert isinstance(function_node, (ast.FunctionDef, ast.AsyncFunctionDef))
    for nested in ast.walk(function_node):
        if (
            isinstance(nested, ast.Call)
            and isinstance(nested.func, ast.Attribute)
            and nested.func.attr == "send_command"
            and nested.args
            and isinstance(nested.args[0], ast.Constant)
            and isinstance(nested.args[0].value, str)
        ):
            return nested.args[0].value
    return function_node.name



def _extract_parameters(function_node: ast.AST) -> tuple[ParameterSpec, ...]:
    assert isinstance(function_node, (ast.FunctionDef, ast.AsyncFunctionDef))
    arguments = function_node.args
    positional = list(arguments.posonlyargs) + list(arguments.args)
    defaults = [None] * (len(positional) - len(arguments.defaults)) + list(arguments.defaults)
    params: list[ParameterSpec] = []

    for arg, default in zip(positional, defaults):
        if arg.arg == "ctx":
            continue
        params.append(
            ParameterSpec(
                name=arg.arg,
                required=default is None,
                annotation=_annotation_to_text(arg.annotation),
                default=_default_to_text(default),
            )
        )

    if arguments.vararg:
        params.append(ParameterSpec(name=arguments.vararg.arg, required=False, annotation="Any"))
    if arguments.kwarg:
        params.append(ParameterSpec(name=arguments.kwarg.arg, required=False, annotation="Any"))
    return tuple(params)



def _parse_tool_specs_from_file(path: Path, module_name: str) -> list[ToolSpec]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    specs: list[ToolSpec] = []
    for node in tree.body:
        if not _is_mcp_tool(node):
            continue
        docstring = ast.get_docstring(node) or ""
        description = docstring.strip().splitlines()[0] if docstring.strip() else node.name
        specs.append(
            ToolSpec(
                name=node.name,
                module=module_name,
                source_file=str(path.relative_to(PACKAGE_ROOT.parent.parent)),
                description=description,
                parameters=_extract_parameters(node),
                command_name=_extract_command_name(node),
            )
        )
    return specs



def discover_tool_specs() -> dict[str, ToolSpec]:
    specs: dict[str, ToolSpec] = {}
    specs_from_server = _parse_tool_specs_from_file(SERVER_FILE, "blender_mcp.server")
    for spec in specs_from_server:
        specs[spec.name] = spec
    for module_name in iter_tool_module_names():
        for spec in _parse_tool_specs_from_file(TOOLS_ROOT / f"{module_name}.py", f"blender_mcp.tools.{module_name}"):
            specs[spec.name] = spec
    return dict(sorted(specs.items()))



def discover_command_to_tool_map() -> dict[str, str]:
    return {spec.command_name: spec.name for spec in discover_tool_specs().values()}



def build_skill_manifest_payload() -> dict[str, Any]:
    tool_specs = discover_tool_specs()
    enum = list(tool_specs)
    tools_payload: dict[str, Any] = {}
    for name, spec in tool_specs.items():
        tools_payload[name] = {
            "description": spec.description,
            "params": {
                param.name: {
                    "required": param.required,
                    **({"type": param.annotation} if param.annotation else {}),
                    **({"default": param.default} if param.default is not None else {}),
                }
                for param in spec.parameters
            },
            "command_name": spec.command_name,
            "module": spec.module,
            "source_file": spec.source_file,
        }
    return {
        "name": "blender_mcp",
        "description": "Interact with Blender and studio pipeline tooling through MCP.",
        "parameters": {
            "type": "object",
            "properties": {
                "tool_name": {
                    "type": "string",
                    "description": "Name of the Blender MCP tool to call",
                    "enum": enum,
                },
                "params": {
                    "type": "object",
                    "description": "Parameters to pass to the tool",
                },
            },
            "required": ["tool_name", "params"],
        },
        "tools": tools_payload,
    }

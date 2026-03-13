"""Validation schemas for MCP command payloads."""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypeAlias

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError, create_model

from .tool_registry import discover_tool_specs


def _ensure_unit_color(color: tuple[float, float, float]) -> tuple[float, float, float]:
    if any(channel < 0.0 or channel > 1.0 for channel in color):
        raise ValueError("color channels must be between 0.0 and 1.0")
    return color


Vector3: TypeAlias = tuple[float, float, float]
Color3: TypeAlias = Annotated[
    tuple[float, float, float], AfterValidator(_ensure_unit_color)
]


class CommandPayloadModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CreatePrimitivePayload(CommandPayloadModel):
    type: Literal["cube", "sphere", "cylinder", "cone", "torus", "plane"]
    name: str | None = Field(default=None, min_length=1)
    size: float | None = Field(default=None, gt=0.0)
    location: Vector3 | None = None
    rotation: Vector3 | None = None
    scale: Vector3 | None = None


class CreateBsdfMaterialPayload(CommandPayloadModel):
    name: str = Field(min_length=1)
    base_color: Color3 | None = None
    metallic: float | None = Field(default=None, ge=0.0, le=1.0)
    roughness: float | None = Field(default=None, ge=0.0, le=1.0)
    specular: float | None = Field(default=None, ge=0.0, le=1.0)
    subsurface: float | None = Field(default=None, ge=0.0, le=1.0)
    subsurface_color: Color3 | None = None
    transmission: float | None = Field(default=None, ge=0.0, le=1.0)
    ior: float | None = Field(default=None, ge=1.0, le=3.0)
    emission_color: Color3 | None = None
    emission_strength: float | None = Field(default=None, ge=0.0)


class CreateAreaLightPayload(CommandPayloadModel):
    name: str = Field(min_length=1)
    light_type: Literal["SQUARE", "RECTANGLE", "CIRCLE", "DISC"] = "RECTANGLE"
    size: float = Field(default=1.0, gt=0.0)
    location: Vector3 | None = None
    rotation: Vector3 | None = None
    energy: float = Field(default=100.0, gt=0.0)
    color: Color3 | None = None


class CreateCompositionCameraPayload(CommandPayloadModel):
    name: str = Field(default="Camera", min_length=1)
    composition: Literal[
        "center",
        "rule_of_thirds",
        "golden_ratio",
        "diagonal",
        "frame",
    ] = "center"
    focal_length: float = Field(default=50.0, gt=0.0)
    location: Vector3 | None = None
    target: Vector3 | None = None


class ExportSceneBundlePayload(CommandPayloadModel):
    slug: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    nextjs_project_root: str = Field(min_length=1)
    mode: Literal["scene", "assets"] = "scene"
    generate_r3f: bool = False


MANUAL_COMMAND_SCHEMAS: dict[str, type[CommandPayloadModel]] = {
    "create_primitive": CreatePrimitivePayload,
    "create_bsdf_material": CreateBsdfMaterialPayload,
    "create_area_light": CreateAreaLightPayload,
    "create_composition_camera": CreateCompositionCameraPayload,
    "export_scene_bundle": ExportSceneBundlePayload,
}


def _annotation_to_type(annotation: str | None) -> Any:
    if not annotation:
        return Any
    normalized = annotation.replace("typing.", "")
    if normalized in {"str", "Optional[str]"}:
        return str | None if "Optional" in normalized else str
    if normalized in {"int", "Optional[int]"}:
        return int | None if "Optional" in normalized else int
    if normalized in {"float", "Optional[float]"}:
        return float | None if "Optional" in normalized else float
    if normalized in {"bool", "Optional[bool]"}:
        return bool | None if "Optional" in normalized else bool
    if "Dict" in normalized or normalized.startswith("dict["):
        return dict[str, Any]
    if "List" in normalized or normalized.startswith("list["):
        return list[Any]
    if "Optional" in normalized or "| None" in normalized:
        return Any | None
    return Any


def _build_dynamic_command_schemas() -> dict[str, type[CommandPayloadModel]]:
    dynamic_schemas: dict[str, type[CommandPayloadModel]] = {}
    for spec in discover_tool_specs().values():
        command_name = spec.command_name
        if command_name in MANUAL_COMMAND_SCHEMAS or command_name in dynamic_schemas:
            continue
        field_definitions: dict[str, tuple[Any, Any]] = {}
        for parameter in spec.parameters:
            field_definitions[parameter.name] = (
                _annotation_to_type(parameter.annotation),
                None,
            )
        dynamic_schemas[command_name] = create_model(
            f"{command_name.title().replace('_', '')}Payload",
            __base__=CommandPayloadModel,
            **field_definitions,
        )
    return dynamic_schemas


COMMAND_SCHEMAS: dict[str, type[CommandPayloadModel]] = {
    **_build_dynamic_command_schemas(),
    **MANUAL_COMMAND_SCHEMAS,
}


def has_command_schema(command_name: str) -> bool:
    return command_name in COMMAND_SCHEMAS


def get_command_schema(command_name: str) -> type[CommandPayloadModel]:
    try:
        return COMMAND_SCHEMAS[command_name]
    except KeyError as exc:
        raise KeyError(
            f"No validation schema registered for command '{command_name}'"
        ) from exc


def validate_command_payload(
    command_name: str, payload: dict[str, Any]
) -> CommandPayloadModel:
    schema = get_command_schema(command_name)
    return schema.model_validate(payload)


__all__ = [
    "COMMAND_SCHEMAS",
    "CommandPayloadModel",
    "CreateAreaLightPayload",
    "CreateBsdfMaterialPayload",
    "CreateCompositionCameraPayload",
    "CreatePrimitivePayload",
    "ExportSceneBundlePayload",
    "get_command_schema",
    "has_command_schema",
    "validate_command_payload",
    "ValidationError",
]

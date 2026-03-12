import pytest
from pydantic import ValidationError

from blender_mcp.schemas import (
    CreateAreaLightPayload,
    CreateBsdfMaterialPayload,
    CreateCompositionCameraPayload,
    CreatePrimitivePayload,
    ExportSceneBundlePayload,
    get_command_schema,
    validate_command_payload,
)


def test_create_primitive_payload_accepts_valid_values():
    payload = CreatePrimitivePayload.model_validate(
        {
            "type": "cube",
            "name": "HeroCube",
            "size": 2.5,
            "location": [1.0, 2.0, 3.0],
            "scale": [1.0, 1.0, 1.0],
        }
    )

    assert payload.type == "cube"
    assert payload.location == (1.0, 2.0, 3.0)


def test_create_primitive_payload_rejects_unknown_type():
    with pytest.raises(ValidationError):
        CreatePrimitivePayload.model_validate({"type": "monkey"})


def test_create_bsdf_material_payload_rejects_invalid_color_channel():
    with pytest.raises(
        ValidationError, match="color channels must be between 0.0 and 1.0"
    ):
        CreateBsdfMaterialPayload.model_validate(
            {"name": "BadMaterial", "base_color": [1.2, 0.2, 0.1]}
        )


def test_create_area_light_payload_requires_positive_energy():
    with pytest.raises(ValidationError):
        CreateAreaLightPayload.model_validate({"name": "SoftBox", "energy": 0.0})


def test_create_composition_camera_payload_accepts_supported_composition():
    payload = CreateCompositionCameraPayload.model_validate(
        {
            "name": "HeroCam",
            "composition": "rule_of_thirds",
            "focal_length": 85.0,
            "target": [0.0, 0.0, 1.0],
        }
    )

    assert payload.composition == "rule_of_thirds"
    assert payload.target == (0.0, 0.0, 1.0)


def test_export_scene_bundle_payload_rejects_invalid_slug():
    with pytest.raises(ValidationError):
        ExportSceneBundlePayload.model_validate(
            {"slug": "Hero Scene", "nextjs_project_root": "C:/tmp/app"}
        )


def test_command_payload_models_forbid_extra_fields():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CreateAreaLightPayload.model_validate(
            {"name": "SoftBox", "energy": 50.0, "unexpected": True}
        )


def test_string_fields_strip_whitespace_before_validation():
    payload = CreateBsdfMaterialPayload.model_validate({"name": "  Hero Material  "})

    assert payload.name == "Hero Material"


def test_required_strings_reject_whitespace_only_values():
    with pytest.raises(ValidationError, match="at least 1 character"):
        CreateBsdfMaterialPayload.model_validate({"name": "   "})


def test_validate_command_payload_dispatches_to_registered_schema():
    payload = validate_command_payload(
        "export_scene_bundle",
        {
            "slug": "hero-scene",
            "nextjs_project_root": "C:/projects/site",
            "mode": "scene",
            "generate_r3f": True,
        },
    )

    assert payload.generate_r3f is True
    assert get_command_schema("create_area_light") is CreateAreaLightPayload


def test_validate_command_payload_rejects_unknown_command():
    with pytest.raises(KeyError, match="No validation schema registered"):
        validate_command_payload("unknown_command", {})

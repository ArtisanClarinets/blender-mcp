import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HANDLERS_ROOT = PROJECT_ROOT / "blender_mcp_addon" / "handlers"


def _load_handler_module(module_basename, fake_bpy):
    module_name = f"blender_mcp_addon.handlers.{module_basename}"
    module_path = HANDLERS_ROOT / f"{module_basename}.py"
    package = types.ModuleType("blender_mcp_addon")
    package.__path__ = [str(PROJECT_ROOT / "blender_mcp_addon")]
    handlers_package = types.ModuleType("blender_mcp_addon.handlers")
    handlers_package.__path__ = [str(HANDLERS_ROOT)]
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)

    with patch.dict(
        sys.modules,
        {
            "bpy": fake_bpy,
            "blender_mcp_addon": package,
            "blender_mcp_addon.handlers": handlers_package,
        },
    ):
        sys.modules.pop(module_name, None)
        spec.loader.exec_module(module)

    return module


def _make_fake_bpy(
    *,
    tripo_enabled=False,
    tripo_api_key=None,
    hyper_enabled=False,
    hyper_api_key=None,
    hyper_mode="main_site",
    hunyuan_enabled=False,
    hunyuan_mode="official",
    hunyuan_api_key=None,
    hunyuan_local_path=None,
):
    settings = types.SimpleNamespace(
        tripo3d_enabled=tripo_enabled,
        tripo3d_api_key=tripo_api_key,
        hyper3d_enabled=hyper_enabled,
        hyper3d_api_key=hyper_api_key,
        hyper3d_mode=hyper_mode,
        hunyuan3d_enabled=hunyuan_enabled,
        hunyuan3d_mode=hunyuan_mode,
        hunyuan3d_api_key=hunyuan_api_key,
        hunyuan3d_local_path=hunyuan_local_path,
    )
    scene = types.SimpleNamespace(blendermcp_settings=settings)
    return types.SimpleNamespace(context=types.SimpleNamespace(scene=scene))


def test_hyper3d_status_preserves_legacy_shape():
    module = _load_handler_module(
        "jobs_hyper3d",
        _make_fake_bpy(
            hyper_enabled=True,
            hyper_api_key="secret",
            hyper_mode="fal",
        ),
    )

    assert module.get_status() == {
        "enabled": True,
        "has_api_key": True,
        "mode": "fal",
        "message": "Hyper3D (fal) ready",
        "api_available": True,
        "modes": ["MAIN_SITE", "FAL_AI"],
    }


def test_hunyuan_status_preserves_legacy_shape():
    module = _load_handler_module(
        "jobs_hunyuan",
        _make_fake_bpy(
            hunyuan_enabled=True,
            hunyuan_mode="local",
            hunyuan_api_key="secret",
            hunyuan_local_path="C:/models/hunyuan",
        ),
    )

    assert module.get_status() == {
        "enabled": True,
        "mode": "local",
        "has_api_key": True,
        "has_local_path": True,
        "message": "Hunyuan3D (local) ready",
        "api_available": True,
    }


def test_hyper3d_job_flow_supports_unified_create_get_import():
    module = _load_handler_module("jobs_hyper3d", _make_fake_bpy())

    created = module.create_job({"text_prompt": "mech"})
    snapshot = module.get_job({"job_id": created["job_id"]})
    polled = module.poll_job_status({"request_id": created["request_id"]})
    imported = module.import_job_result(
        {"job_id": created["job_id"], "name": "Mech", "target_size": 1.25}
    )

    assert snapshot["status"] == "pending"
    assert polled["status"] == "COMPLETED"
    assert polled["model_url"].endswith(f"{created['job_id']}.glb")
    assert imported == {
        "status": "success",
        "provider": "hyper3d",
        "name": "Mech",
        "imported": True,
        "imported_objects": ["Mech"],
        "deferred_import": True,
        "job_id": created["job_id"],
        "source": polled["model_url"],
        "model_url": polled["model_url"],
        "target_size": 1.25,
        "request_id": created["request_id"],
        "task_uuid": created["job_id"],
    }


def test_hyper3d_create_job_rejects_empty_or_impossible_payloads():
    module = _load_handler_module("jobs_hyper3d", _make_fake_bpy())

    with pytest.raises(
        ValueError,
        match="text_prompt, input_image_paths, or input_image_urls is required",
    ):
        module.create_job({})

    with pytest.raises(ValueError, match="input_image_urls must be a non-empty list"):
        module.create_job({"input_image_urls": "memory://reference.png"})


def test_hunyuan_job_flow_supports_unified_create_get_import():
    module = _load_handler_module("jobs_hunyuan", _make_fake_bpy())

    created = module.create_job({"text_prompt": "vase"})
    snapshot = module.get_job({"job_id": created["job_id"]})
    polled = module.poll_job_status({"job_id": created["job_id"]})
    imported = module.import_job_result(
        {"job_id": created["job_id"], "name": "Vase", "target_size": 0.4}
    )

    assert snapshot["status"] == "pending"
    assert polled["status"] == "DONE"
    assert polled["zip_file_url"].endswith(f"{created['job_id']}.zip")
    assert imported == {
        "status": "success",
        "provider": "hunyuan3d",
        "name": "Vase",
        "imported": True,
        "imported_objects": ["Vase"],
        "deferred_import": True,
        "job_id": created["job_id"],
        "source": polled["zip_file_url"],
        "target_size": 0.4,
        "zip_file_url": polled["zip_file_url"],
    }


def test_hunyuan_create_job_rejects_missing_inputs():
    module = _load_handler_module("jobs_hunyuan", _make_fake_bpy())

    with pytest.raises(ValueError, match="text_prompt or input_image_url is required"):
        module.create_job({})

    with pytest.raises(ValueError, match="text_prompt or input_image_url is required"):
        module.create_job({"text_prompt": "   ", "input_image_url": "   "})


def test_hunyuan_generation_accepts_image_without_text_prompt():
    module = _load_handler_module("jobs_hunyuan", _make_fake_bpy())

    created = module.generate_model({"input_image_url": "memory://reference.png"})
    snapshot = module.get_job({"job_id": created["job_id"]})

    assert created == {
        "job_id": created["job_id"],
        "status": "RUN",
        "message": "Generation job created",
    }
    assert snapshot["payload"] == {"input_image_url": "memory://reference.png"}


def test_tripo3d_job_flow_and_status_support_unified_import():
    module = _load_handler_module(
        "jobs_tripo3d",
        _make_fake_bpy(tripo_enabled=True, tripo_api_key="secret"),
    )

    status = module.get_status()
    created = module.create_job({"text_prompt": "dragon"})
    snapshot = module.get_job({"job_id": created["job_id"]})
    polled = module.poll_job_status({"task_id": created["task_id"]})
    imported = module.import_job_result(
        {"job_id": created["job_id"], "name": "Dragon", "target_size": 2.0}
    )

    assert status == {"enabled": True, "has_api_key": True, "message": "Tripo3D ready"}
    assert snapshot["status"] == "pending"
    assert polled["status"] == "completed"
    assert imported == {
        "status": "success",
        "provider": "tripo3d",
        "name": "Dragon",
        "imported": True,
        "imported_objects": ["Dragon"],
        "deferred_import": True,
        "job_id": created["job_id"],
        "source": polled["model_url"],
        "target_size": 2.0,
        "model_url": polled["model_url"],
        "task_id": created["task_id"],
    }

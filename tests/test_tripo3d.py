import asyncio
import json


def test_generate_tripo3d_model_routes_prompt(
    load_tool_module, mock_blender_connection
):
    mock_blender_connection.send_command.return_value = {
        "job_id": "job_tripo",
        "task_id": "job_tripo",
        "status": "PENDING",
    }

    tripo3d = load_tool_module("blender_mcp.tools.tripo3d")

    result = asyncio.run(
        tripo3d.generate_tripo3d_model(None, text_prompt="stylized robot")
    )

    assert json.loads(result)["task_id"] == "job_tripo"
    mock_blender_connection.send_command.assert_called_once_with(
        "generate_tripo3d_model",
        {"text_prompt": "stylized robot"},
    )


def test_generate_tripo3d_model_requires_prompt_or_image(
    load_tool_module, mock_blender_connection
):
    tripo3d = load_tool_module("blender_mcp.tools.tripo3d")

    result = asyncio.run(tripo3d.generate_tripo3d_model(None))

    assert json.loads(result) == {
        "error": "Either text_prompt or image_url must be provided"
    }
    mock_blender_connection.send_command.assert_not_called()


def test_get_tripo3d_status_routes_command(load_tool_module, mock_blender_connection):
    mock_blender_connection.send_command.return_value = {
        "enabled": True,
        "has_api_key": True,
        "message": "Tripo3D ready",
    }

    tripo3d = load_tool_module("blender_mcp.tools.tripo3d")

    result = asyncio.run(tripo3d.get_tripo3d_status(None))

    assert json.loads(result) == {
        "enabled": True,
        "has_api_key": True,
        "message": "Tripo3D ready",
    }
    mock_blender_connection.send_command.assert_called_once_with(
        "get_tripo3d_status",
        {},
    )


def test_poll_and_import_tripo3d_model(load_tool_module, mock_blender_connection):
    mock_blender_connection.send_command.side_effect = [
        {"task_id": "job_tripo", "status": "completed"},
        {"status": "success", "name": "Robot"},
    ]

    tripo3d = load_tool_module("blender_mcp.tools.tripo3d")

    poll_result = asyncio.run(tripo3d.poll_tripo3d_status(None, task_id="job_tripo"))
    import_result = asyncio.run(
        tripo3d.import_tripo3d_model(
            None,
            model_url="memory://tripo3d/job_tripo.glb",
            name="Robot",
        )
    )

    assert json.loads(poll_result)["status"] == "completed"
    assert json.loads(import_result)["name"] == "Robot"
    assert mock_blender_connection.send_command.call_args_list[0].args == (
        "poll_tripo3d_status",
        {"task_id": "job_tripo"},
    )
    assert mock_blender_connection.send_command.call_args_list[1].args == (
        "import_tripo3d_model",
        {"model_url": "memory://tripo3d/job_tripo.glb", "name": "Robot"},
    )

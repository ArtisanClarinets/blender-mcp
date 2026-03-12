import asyncio
import json


def test_create_job_supports_tripo3d_provider(
    load_tool_module, mock_blender_connection
):
    mock_blender_connection.send_command.return_value = {
        "job_id": "job_123",
        "provider": "tripo3d",
        "status": "pending",
    }

    jobs = load_tool_module("blender_mcp.tools.jobs")

    result = asyncio.run(
        jobs.create_job(
            None,
            provider="tripo3d",
            payload={"text_prompt": "wooden chair"},
        )
    )

    assert json.loads(result) == {
        "job_id": "job_123",
        "provider": "tripo3d",
        "status": "pending",
    }
    mock_blender_connection.send_command.assert_called_once_with(
        "create_job",
        {"provider": "tripo3d", "payload": {"text_prompt": "wooden chair"}},
    )


def test_import_job_result_preserves_zero_target_size(
    load_tool_module, mock_blender_connection
):
    mock_blender_connection.send_command.return_value = {
        "status": "success",
        "job_id": "job_123",
    }

    jobs = load_tool_module("blender_mcp.tools.jobs")

    result = asyncio.run(
        jobs.import_job_result(None, job_id="job_123", name="Chair", target_size=0.0)
    )

    assert json.loads(result)["job_id"] == "job_123"
    mock_blender_connection.send_command.assert_called_once_with(
        "import_job_result",
        {"job_id": "job_123", "name": "Chair", "target_size": 0.0},
    )


def test_get_job_routes_job_id(load_tool_module, mock_blender_connection):
    mock_blender_connection.send_command.return_value = {
        "job_id": "job_123",
        "provider": "hyper3d",
        "status": "COMPLETED",
    }

    jobs = load_tool_module("blender_mcp.tools.jobs")

    result = asyncio.run(jobs.get_job(None, job_id="job_123"))

    assert json.loads(result) == {
        "job_id": "job_123",
        "provider": "hyper3d",
        "status": "COMPLETED",
    }
    mock_blender_connection.send_command.assert_called_once_with(
        "get_job",
        {"job_id": "job_123"},
    )

import importlib
import sys
import types
from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


class DummyMCP:
    @staticmethod
    def tool() -> Callable[[Callable], Callable]:
        return lambda func: func


@pytest.fixture(scope="session")
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def mock_blender_connection() -> Mock:
    return Mock(name="mock_blender_connection")


@pytest.fixture
def server_stub(mock_blender_connection: Mock) -> types.ModuleType:
    module = types.ModuleType("blender_mcp.server")
    module.BlenderConnection = object
    module.get_blender_connection = lambda: mock_blender_connection
    module.mcp = DummyMCP()
    return module


@pytest.fixture
def load_tool_module(
    server_stub: types.ModuleType,
) -> Callable[[str], types.ModuleType]:
    loaded_modules: list[tuple[str, types.ModuleType | None]] = []

    def _load(module_name: str) -> types.ModuleType:
        previous_module = sys.modules.pop(module_name, None)
        loaded_modules.append((module_name, previous_module))

        with patch.dict(sys.modules, {"blender_mcp.server": server_stub}):
            return importlib.import_module(module_name)

    yield _load

    for module_name, previous_module in reversed(loaded_modules):
        sys.modules.pop(module_name, None)
        if previous_module is not None:
            sys.modules[module_name] = previous_module

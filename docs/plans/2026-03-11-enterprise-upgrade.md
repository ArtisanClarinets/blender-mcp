# Blender MCP Enterprise Upgrade Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform Blender MCP from a functional prototype to an enterprise-ready system with comprehensive testing, reliability patterns, observability, security, and complete tool implementations.

**Architecture:** Three-tier architecture with transport layer (TCP/WebSocket), service layer (business logic with validation), and integration layer (external APIs with resilience patterns). Implements async-first design with proper sync bridges.

**Tech Stack:** Python 3.10+, FastMCP, pytest, pydantic, structlog, tenacity, prometheus-client, websockets, SQLite/Redis

---

## Executive Summary

### Current State Analysis
- **Strengths:** Functional MCP server, Blender addon with socket communication, multiple asset integrations
- **Critical Gaps:** 
  - Missing job management handlers (`create_job`, `get_job`, `import_job_result`)
  - No formal testing framework
  - Inconsistent error handling
  - No validation schemas
  - Missing enterprise features (auth, audit, rate limiting)
  - Tripo3D integration defined but not implemented

### Target State
- 80%+ test coverage with pytest
- JSON Schema validation for all inputs
- Connection resilience with retry/circuit breaker
- Structured logging with correlation IDs
- Health checks and metrics
- Complete tool implementations
- Comprehensive documentation

---

## Phase 1: Foundation (Testing & Validation)

### Task 1.1: Set Up Testing Infrastructure

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/__init__.py`
- Modify: `pyproject.toml`

**Step 1: Add test dependencies**

```toml
# Add to pyproject.toml dependencies
dependencies = [
    "mcp[cli]>=1.3.0",
    "supabase>=2.0.0",
    "tomli>=2.0.0",
    "pydantic>=2.0.0",
    "structlog>=24.0.0",
    "tenacity>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "httpx>=0.25.0",
    "respx>=0.20.0",
]
```

**Step 2: Create pytest configuration**

```python
# tests/conftest.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def mock_blender_connection():
    """Mock Blender connection for testing"""
    conn = Mock()
    conn.send_command = Mock(return_value={"status": "success", "result": {}})
    conn.connect = Mock(return_value=True)
    conn.disconnect = Mock()
    return conn

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset global singletons between tests"""
    yield
    # Reset any global state here
```

**Step 3: Create test utilities**

```python
# tests/utils.py
import json
from typing import Dict, Any

def assert_valid_json_response(response: str) -> Dict[str, Any]:
    """Assert that response is valid JSON and return parsed data"""
    try:
        data = json.loads(response)
        assert isinstance(data, dict)
        return data
    except json.JSONDecodeError as e:
        raise AssertionError(f"Response is not valid JSON: {e}\nResponse: {response}")

def assert_success_response(response: str) -> Dict[str, Any]:
    """Assert that response indicates success"""
    data = assert_valid_json_response(response)
    assert "error" not in data, f"Response contains error: {data.get('error')}"
    return data

def assert_error_response(response: str, expected_code: str = None) -> Dict[str, Any]:
    """Assert that response indicates error"""
    data = assert_valid_json_response(response)
    assert "error" in data, f"Expected error response but got: {data}"
    if expected_code:
        assert data.get("error", {}).get("code") == expected_code
    return data
```

**Step 4: Verify setup**

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests (should pass with no tests collected)
pytest tests/ -v
```

**Step 5: Commit**

```bash
git add pyproject.toml tests/
git commit -m "test: set up pytest infrastructure with async support"
```

---

### Task 1.2: Implement Pydantic Validation Schemas

**Files:**
- Create: `src/blender_mcp/schemas.py`
- Create: `tests/test_schemas.py`

**Step 1: Define request/response schemas**

```python
# src/blender_mcp/schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from enum import Enum

class PrimitiveType(str, Enum):
    CUBE = "cube"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    CONE = "cone"
    TORUS = "torus"
    PLANE = "plane"

class LightType(str, Enum):
    POINT = "point"
    SUN = "sun"
    SPOT = "spot"
    AREA = "area"

class Vector3(BaseModel):
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    z: float = Field(..., description="Z coordinate")
    
    @validator('*')
    def validate_finite(cls, v):
        import math
        if not math.isfinite(v):
            raise ValueError(f"Value must be finite, got {v}")
        return v

class CreatePrimitiveRequest(BaseModel):
    type: PrimitiveType = Field(..., description="Type of primitive to create")
    name: Optional[str] = Field(None, max_length=64, description="Object name")
    size: Optional[float] = Field(None, gt=0, description="Size parameter")
    location: Optional[List[float]] = Field(None, min_items=3, max_items=3, description="[x, y, z] location")
    rotation: Optional[List[float]] = Field(None, min_items=3, max_items=3, description="[x, y, z] rotation in radians")
    scale: Optional[List[float]] = Field(None, min_items=3, max_items=3, description="[x, y, z] scale")
    
    @validator('location', 'rotation', 'scale')
    def validate_vector3(cls, v):
        if v is not None:
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError("All vector components must be numbers")
        return v

class CreateLightRequest(BaseModel):
    type: LightType = Field(..., description="Type of light")
    energy: float = Field(..., gt=0, description="Light energy/strength")
    color: Optional[List[float]] = Field(None, min_items=3, max_items=3, description="[r, g, b] color (0-1)")
    location: Optional[List[float]] = Field(None, min_items=3, max_items=3, description="[x, y, z] location")
    rotation: Optional[List[float]] = Field(None, min_items=3, max_items=3, description="[x, y, z] rotation")
    
    @validator('color')
    def validate_color(cls, v):
        if v is not None:
            if not all(0 <= x <= 1 for x in v):
                raise ValueError("Color values must be between 0 and 1")
        return v

class SetTransformRequest(BaseModel):
    target_id: str = Field(..., min_length=1, max_length=128, description="Object name or ID")
    location: Optional[List[float]] = Field(None, min_items=3, max_items=3)
    rotation: Optional[List[float]] = Field(None, min_items=3, max_items=3)
    scale: Optional[List[float]] = Field(None, min_items=3, max_items=3)
    apply: bool = Field(False, description="Whether to apply the transform")

class DownloadPolyhavenAssetRequest(BaseModel):
    asset_id: str = Field(..., min_length=1, description="Asset ID from PolyHaven")
    asset_type: Literal["hdris", "textures", "models"] = Field(..., description="Type of asset")
    resolution: str = Field("2k", pattern=r"^[1248]k$", description="Resolution (1k, 2k, 4k, 8k)")
    file_format: Optional[str] = Field(None, description="Optional file format")

class SearchSketchfabModelsRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=256, description="Search query")
    categories: Optional[str] = Field(None, description="Comma-separated categories")
    count: int = Field(20, ge=1, le=100, description="Max results to return")
    downloadable: bool = Field(True, description="Only downloadable models")

class GenerateHyper3DModelRequest(BaseModel):
    text_prompt: Optional[str] = Field(None, min_length=1, max_length=1000, description="Text description")
    input_image_paths: Optional[List[str]] = Field(None, description="Absolute paths to images")
    input_image_urls: Optional[List[str]] = Field(None, description="URLs to images")
    bbox_condition: Optional[List[float]] = Field(None, min_items=3, max_items=3, description="[L, W, H] ratio")
    
    @validator('text_prompt')
    def validate_prompt_or_images(cls, v, values):
        has_images = values.get('input_image_paths') or values.get('input_image_urls')
        if not v and not has_images:
            raise ValueError("Either text_prompt or images must be provided")
        if v and has_images:
            raise ValueError("Cannot provide both text_prompt and images")
        return v

class ExportGLBRequest(BaseModel):
    target: Literal["scene", "selection", "collection"] = Field("scene", description="What to export")
    name: str = Field("export", min_length=1, max_length=128, description="File name")
    output_dir: str = Field("exports", description="Output directory")
    draco: bool = Field(True, description="Use Draco compression")
    texture_embed: bool = Field(True, description="Embed textures")
    y_up: bool = Field(True, description="Use Y-up coordinate system")

class ExportSceneBundleRequest(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z0-9-]+$", description="Unique identifier")
    nextjs_project_root: str = Field(..., description="Path to Next.js project root")
    mode: Literal["scene", "assets"] = Field("scene", description="Export mode")
    generate_r3f: bool = Field(False, description="Generate React Three Fiber components")

# Response schemas
class SuccessResponse(BaseModel):
    ok: bool = True
    data: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    ok: bool = False
    error: Dict[str, Any] = Field(..., description="Error details")
    request_id: Optional[str] = None
```

**Step 2: Write tests for schemas**

```python
# tests/test_schemas.py
import pytest
from blender_mcp.schemas import (
    CreatePrimitiveRequest,
    CreateLightRequest,
    SetTransformRequest,
    DownloadPolyhavenAssetRequest,
    SearchSketchfabModelsRequest,
    GenerateHyper3DModelRequest,
)
from pydantic import ValidationError

class TestCreatePrimitiveRequest:
    def test_valid_cube(self):
        req = CreatePrimitiveRequest(type="cube", name="MyCube")
        assert req.type == "cube"
        assert req.name == "MyCube"
    
    def test_invalid_primitive_type(self):
        with pytest.raises(ValidationError) as exc_info:
            CreatePrimitiveRequest(type="invalid")
        assert "type" in str(exc_info.value)
    
    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            CreatePrimitiveRequest(type="cube", name="x" * 100)
    
    def test_invalid_size(self):
        with pytest.raises(ValidationError):
            CreatePrimitiveRequest(type="cube", size=-1)
    
    def test_invalid_location_length(self):
        with pytest.raises(ValidationError):
            CreatePrimitiveRequest(type="cube", location=[1, 2])
    
    def test_non_finite_values(self):
        with pytest.raises(ValidationError):
            CreatePrimitiveRequest(type="cube", location=[float('inf'), 0, 0])

class TestCreateLightRequest:
    def test_valid_point_light(self):
        req = CreateLightRequest(type="point", energy=100)
        assert req.type == "point"
        assert req.energy == 100
    
    def test_invalid_color_range(self):
        with pytest.raises(ValidationError):
            CreateLightRequest(type="point", energy=100, color=[1.5, 0, 0])
    
    def test_zero_energy(self):
        with pytest.raises(ValidationError):
            CreateLightRequest(type="point", energy=0)

class TestSetTransformRequest:
    def test_valid_transform(self):
        req = SetTransformRequest(
            target_id="Cube",
            location=[1, 2, 3],
            rotation=[0, 0, 1.57]
        )
        assert req.target_id == "Cube"
        assert req.apply is False

class TestDownloadPolyhavenAssetRequest:
    def test_valid_request(self):
        req = DownloadPolyhavenAssetRequest(
            asset_id="rock_01",
            asset_type="textures",
            resolution="4k"
        )
        assert req.resolution == "4k"
    
    def test_invalid_resolution(self):
        with pytest.raises(ValidationError):
            DownloadPolyhavenAssetRequest(
                asset_id="rock_01",
                asset_type="textures",
                resolution="10k"
            )

class TestSearchSketchfabModelsRequest:
    def test_valid_search(self):
        req = SearchSketchfabModelsRequest(query="car", count=50)
        assert req.query == "car"
        assert req.count == 50
    
    def test_count_out_of_range(self):
        with pytest.raises(ValidationError):
            SearchSketchfabModelsRequest(query="car", count=200)

class TestGenerateHyper3DModelRequest:
    def test_valid_text_prompt(self):
        req = GenerateHyper3DModelRequest(text_prompt="A red car")
        assert req.text_prompt == "A red car"
    
    def test_valid_image_paths(self):
        req = GenerateHyper3DModelRequest(input_image_paths=["/path/to/image.jpg"])
        assert req.input_image_paths == ["/path/to/image.jpg"]
    
    def test_both_prompt_and_images(self):
        with pytest.raises(ValidationError):
            GenerateHyper3DModelRequest(
                text_prompt="A car",
                input_image_paths=["/path/to/image.jpg"]
            )
    
    def test_neither_prompt_nor_images(self):
        with pytest.raises(ValidationError):
            GenerateHyper3DModelRequest()
```

**Step 3: Run tests**

```bash
pytest tests/test_schemas.py -v
```

**Step 4: Commit**

```bash
git add src/blender_mcp/schemas.py tests/test_schemas.py
git commit -m "feat: add pydantic validation schemas for all tool inputs"
```

---

### Task 1.3: Add Structured Logging

**Files:**
- Create: `src/blender_mcp/logging_config.py`
- Modify: `src/blender_mcp/server.py`

**Step 1: Create logging configuration**

```python
# src/blender_mcp/logging_config.py
import structlog
import logging
import sys
from typing import Any, Dict

# Configure standard library logging
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if sys.stderr.isatty() else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with the given name"""
    return structlog.get_logger(name)

class LogContext:
    """Context manager for adding context to logs"""
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.logger = structlog.get_logger()
    
    def __enter__(self):
        self.logger = self.logger.bind(**self.context)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def log_tool_call(tool_name: str, request_id: str = None, **context):
    """Decorator context for logging tool calls"""
    return LogContext(tool=tool_name, request_id=request_id, **context)
```

**Step 2: Update server.py to use structured logging**

```python
# In src/blender_mcp/server.py
# Replace existing logging setup with:
from .logging_config import get_logger, LogContext

logger = get_logger("BlenderMCPServer")

# Update tool implementations to use structured logging
@telemetry_tool("create_primitive")
@mcp.tool()
async def create_primitive(
    ctx: Context,
    type: str,
    name: Optional[str] = None,
    size: Optional[float] = None,
    location: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
    scale: Optional[List[float]] = None,
) -> str:
    """Create a primitive object in the scene."""
    request_id = str(uuid.uuid4())
    
    with LogContext(tool="create_primitive", request_id=request_id, primitive_type=type):
        logger.info("Creating primitive", name=name, location=location)
        
        try:
            # Validate input
            from .schemas import CreatePrimitiveRequest
            request = CreatePrimitiveRequest(
                type=type,
                name=name,
                size=size,
                location=location,
                rotation=rotation,
                scale=scale
            )
            
            blender = get_blender_connection()
            result = blender.send_command("create_primitive", request.dict(exclude_none=True))
            
            logger.info("Primitive created successfully", result=result)
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error("Failed to create primitive", error=str(e))
            return json.dumps({"error": str(e)})
```

**Step 3: Test logging configuration**

```python
# tests/test_logging.py
import pytest
from blender_mcp.logging_config import get_logger, LogContext
import structlog

class TestLogging:
    def test_get_logger(self):
        logger = get_logger("test")
        assert logger is not None
    
    def test_log_context(self, caplog):
        with LogContext(request_id="123", tool="test") as logger:
            logger.info("Test message")
            # Verify context is bound
```

**Step 4: Commit**

```bash
git add src/blender_mcp/logging_config.py tests/test_logging.py
git commit -m "feat: add structured logging with structlog"
```

---

## Phase 2: Reliability & Observability

### Task 2.1: Implement Connection Resilience

**Files:**
- Create: `src/blender_mcp/resilience.py`
- Modify: `src/blender_mcp/server.py`

**Step 1: Create retry and circuit breaker decorators**

```python
# src/blender_mcp/resilience.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from functools import wraps
import time
import logging
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger("BlenderMCP.Resilience")

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """Circuit breaker pattern for external API calls"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state")
                return True
            return False
        
        return True  # HALF_OPEN
    
    def record_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failures} failures")
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.can_execute():
                raise CircuitBreakerOpen("Circuit breaker is open")
            
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except self.expected_exception as e:
                self.record_failure()
                raise
        
        return wrapper

class CircuitBreakerOpen(Exception):
    pass

# Pre-configured retry decorators
blender_connection_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)

api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True
)
```

**Step 2: Update BlenderConnection with retry logic**

```python
# In src/blender_mcp/server.py
from .resilience import blender_connection_retry, CircuitBreaker

class BlenderConnection:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None
        self._circuit_breaker = CircuitBreaker(failure_threshold=3)
    
    @blender_connection_retry
    def connect(self) -> bool:
        """Connect to Blender with retry"""
        if self.sock:
            return True
        
        if not self._circuit_breaker.can_execute():
            raise ConnectionError("Circuit breaker is open - too many connection failures")
        
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10.0)  # Connection timeout
            self.sock.connect((self.host, self.port))
            self._circuit_breaker.record_success()
            logger.info(f"Connected to Blender at {self.host}:{self.port}")
            return True
        except Exception as e:
            self._circuit_breaker.record_failure()
            logger.error(f"Failed to connect to Blender: {e}")
            self.sock = None
            raise
    
    def send_command(self, command_type: str, params: Dict[str, Any] = None, 
                     request_id: str = None, idempotency_key: str = None) -> Dict[str, Any]:
        """Send command with automatic retry and circuit breaker"""
        # Implementation with retry logic
        pass
```

**Step 3: Write tests for resilience**

```python
# tests/test_resilience.py
import pytest
from unittest.mock import Mock, patch
from blender_mcp.resilience import CircuitBreaker, CircuitBreakerOpen
import time

class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state.value == "closed"
        assert cb.can_execute() is True
    
    def test_opens_after_failures(self):
        cb = CircuitBreaker(failure_threshold=3)
        
        @cb
        def failing_func():
            raise ValueError("Test error")
        
        # First 3 calls should raise ValueError
        for _ in range(3):
            with pytest.raises(ValueError):
                failing_func()
        
        # Circuit should be open now
        assert cb.state.value == "open"
        
        # Next call should raise CircuitBreakerOpen
        with pytest.raises(CircuitBreakerOpen):
            failing_func()
    
    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        @cb
        def failing_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_func()
        
        assert cb.state.value == "open"
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Should be able to execute now (half-open)
        assert cb.can_execute() is True
    
    def test_closes_on_success(self):
        cb = CircuitBreaker(failure_threshold=2)
        call_count = 0
        
        @cb
        def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Fail")
            return "success"
        
        with pytest.raises(ValueError):
            sometimes_fails()
        
        result = sometimes_fails()
        assert result == "success"
        assert cb.state.value == "closed"
```

**Step 4: Commit**

```bash
git add src/blender_mcp/resilience.py tests/test_resilience.py
git commit -m "feat: add connection resilience with retry and circuit breaker"
```

---

### Task 2.2: Implement Health Checks and Metrics

**Files:**
- Create: `src/blender_mcp/health.py`
- Create: `src/blender_mcp/metrics.py`
- Modify: `src/blender_mcp/server.py`

**Step 1: Create health check system**

```python
# src/blender_mcp/health.py
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import time

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    latency_ms: float
    metadata: Optional[Dict] = None

class HealthMonitor:
    """Health monitoring system"""
    
    def __init__(self):
        self.checks: Dict[str, HealthCheck] = {}
        self._check_functions: Dict[str, callable] = {}
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check function"""
        self._check_functions[name] = check_func
    
    async def run_checks(self) -> Dict[str, HealthCheck]:
        """Run all registered health checks"""
        import asyncio
        
        for name, check_func in self._check_functions.items():
            start_time = time.time()
            try:
                result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                latency = (time.time() - start_time) * 1000
                
                self.checks[name] = HealthCheck(
                    name=name,
                    status=result.get("status", HealthStatus.HEALTHY),
                    message=result.get("message", "OK"),
                    timestamp=datetime.utcnow(),
                    latency_ms=latency,
                    metadata=result.get("metadata")
                )
            except Exception as e:
                latency = (time.time() - start_time) * 1000
                self.checks[name] = HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    timestamp=datetime.utcnow(),
                    latency_ms=latency
                )
        
        return self.checks
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall health status"""
        if not self.checks:
            return HealthStatus.HEALTHY
        
        statuses = [check.status for check in self.checks.values()]
        
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        if any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON response"""
        return {
            "status": self.get_overall_status().value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                name: {
                    "status": check.status.value,
                    "message": check.message,
                    "timestamp": check.timestamp.isoformat(),
                    "latency_ms": check.latency_ms,
                    "metadata": check.metadata
                }
                for name, check in self.checks.items()
            }
        }

# Global health monitor
health_monitor = HealthMonitor()
```

**Step 2: Create metrics collection**

```python
# src/blender_mcp/metrics.py
from typing import Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict
import time
from contextlib import contextmanager

@dataclass
class Counter:
    value: int = 0
    
    def inc(self, amount: int = 1):
        self.value += amount

@dataclass
class Histogram:
    buckets: list = field(default_factory=lambda: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10])
    observations: list = field(default_factory=list)
    
    def observe(self, value: float):
        self.observations.append(value)
    
    def get_bucket_counts(self) -> Dict[str, int]:
        counts = {}
        for bucket in self.buckets:
            counts[f"le_{bucket}"] = sum(1 for obs in self.observations if obs <= bucket)
        counts["le_inf"] = len(self.observations)
        return counts

class MetricsRegistry:
    """Simple metrics registry"""
    
    def __init__(self):
        self.counters: Dict[str, Counter] = defaultdict(Counter)
        self.histograms: Dict[str, Histogram] = defaultdict(Histogram)
        self.gauges: Dict[str, float] = {}
    
    def counter(self, name: str) -> Counter:
        return self.counters[name]
    
    def histogram(self, name: str) -> Histogram:
        return self.histograms[name]
    
    def gauge(self, name: str, value: float):
        self.gauges[name] = value
    
    def to_prometheus_format(self) -> str:
        """Export metrics in Prometheus text format"""
        lines = []
        
        # Counters
        for name, counter in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {counter.value}")
        
        # Histograms
        for name, histogram in self.histograms.items():
            lines.append(f"# TYPE {name} histogram")
            bucket_counts = histogram.get_bucket_counts()
            for bucket, count in bucket_counts.items():
                if bucket == "le_inf":
                    lines.append(f'{name}_bucket{{le="+Inf"}} {count}')
                else:
                    bucket_val = bucket.replace("le_", "")
                    lines.append(f'{name}_bucket{{le="{bucket_val}"}} {count}')
            lines.append(f"{name}_count {len(histogram.observations)}")
            if histogram.observations:
                lines.append(f"{name}_sum {sum(histogram.observations)}")
        
        # Gauges
        for name, value in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        return "\n".join(lines)

# Global registry
metrics = MetricsRegistry()

@contextmanager
def timed(metric_name: str):
    """Context manager for timing operations"""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        metrics.histogram(metric_name).observe(duration)
```

**Step 3: Add health check tool to server**

```python
# In src/blender_mcp/server.py
from .health import health_monitor, HealthStatus
from .metrics import metrics, timed

# Register health checks
def register_health_checks():
    def check_blender_connection():
        try:
            blender = get_blender_connection()
            return {"status": HealthStatus.HEALTHY, "message": "Connected"}
        except Exception as e:
            return {"status": HealthStatus.UNHEALTHY, "message": str(e)}
    
    health_monitor.register_check("blender_connection", check_blender_connection)

@telemetry_tool("health_check")
@mcp.tool()
async def health_check(ctx: Context) -> str:
    """Get system health status"""
    checks = await health_monitor.run_checks()
    return json.dumps(health_monitor.to_dict(), indent=2)

@telemetry_tool("metrics")
@mcp.tool()
async def get_metrics(ctx: Context) -> str:
    """Get Prometheus-formatted metrics"""
    return metrics.to_prometheus_format()

# Update tool implementations to track metrics
@telemetry_tool("create_primitive")
@mcp.tool()
async def create_primitive(...) -> str:
    with timed("blender_tool_duration_seconds"):
        metrics.counter("blender_tool_calls_total").inc()
        # ... rest of implementation
```

**Step 4: Write tests**

```python
# tests/test_health.py
import pytest
from blender_mcp.health import HealthMonitor, HealthStatus, HealthCheck
from datetime import datetime

class TestHealthMonitor:
    @pytest.mark.asyncio
    async def test_run_checks(self):
        monitor = HealthMonitor()
        
        def mock_check():
            return {"status": HealthStatus.HEALTHY, "message": "OK"}
        
        monitor.register_check("test", mock_check)
        checks = await monitor.run_checks()
        
        assert "test" in checks
        assert checks["test"].status == HealthStatus.HEALTHY
    
    def test_overall_status_healthy(self):
        monitor = HealthMonitor()
        monitor.checks["test"] = HealthCheck(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
            timestamp=datetime.utcnow(),
            latency_ms=10
        )
        assert monitor.get_overall_status() == HealthStatus.HEALTHY

# tests/test_metrics.py
from blender_mcp.metrics import MetricsRegistry, timed
import time

class TestMetrics:
    def test_counter(self):
        registry = MetricsRegistry()
        registry.counter("test").inc()
        registry.counter("test").inc(5)
        assert registry.counters["test"].value == 6
    
    def test_histogram(self):
        registry = MetricsRegistry()
        registry.histogram("duration").observe(0.1)
        registry.histogram("duration").observe(0.5)
        assert len(registry.histograms["duration"].observations) == 2
    
    def test_prometheus_format(self):
        registry = MetricsRegistry()
        registry.counter("requests").inc(10)
        output = registry.to_prometheus_format()
        assert "requests 10" in output
```

**Step 5: Commit**

```bash
git add src/blender_mcp/health.py src/blender_mcp/metrics.py tests/test_health.py tests/test_metrics.py
git commit -m "feat: add health checks and metrics collection"
```

---

## Phase 3: Complete Tool Implementations

### Task 3.1: Implement Missing Job Management Handlers in Addon

**Files:**
- Modify: `addon.py` (add handlers)
- Create: `blender_mcp_addon/handlers/jobs.py`

**Step 1: Create unified job management system**

```python
# blender_mcp_addon/handlers/jobs.py
import bpy
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

# In-memory job store (would be SQLite/Redis in production)
_job_store: Dict[str, Dict[str, Any]] = {}

def create_job(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new async job"""
    provider = params.get("provider")
    payload = params.get("payload", {})
    
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    
    job = {
        "id": job_id,
        "provider": provider,
        "status": "pending",
        "payload": payload,
        "result": None,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "progress": 0,
    }
    
    _job_store[job_id] = job
    
    # Dispatch to appropriate provider
    if provider == "hyper3d":
        _dispatch_hyper3d_job(job)
    elif provider == "hunyuan3d":
        _dispatch_hunyuan3d_job(job)
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    return {
        "job_id": job_id,
        "provider": provider,
        "status": "pending"
    }

def get_job(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get job status"""
    job_id = params.get("job_id")
    
    if job_id not in _job_store:
        raise ValueError(f"Job not found: {job_id}")
    
    job = _job_store[job_id]
    
    # Poll provider for updates if job is in progress
    if job["status"] in ["pending", "running"]:
        _update_job_status(job)
    
    return {
        "job_id": job["id"],
        "provider": job["provider"],
        "status": job["status"],
        "progress": job["progress"],
        "result": job["result"],
        "error": job["error"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
    }

def import_job_result(params: Dict[str, Any]) -> Dict[str, Any]:
    """Import completed job result into scene"""
    job_id = params.get("job_id")
    name = params.get("name")
    target_size = params.get("target_size")
    
    if job_id not in _job_store:
        raise ValueError(f"Job not found: {job_id}")
    
    job = _job_store[job_id]
    
    if job["status"] != "completed":
        raise ValueError(f"Job is not completed. Current status: {job['status']}")
    
    if not job["result"]:
        raise ValueError("Job has no result to import")
    
    # Import based on provider
    if job["provider"] == "hyper3d":
        return _import_hyper3d_result(job, name, target_size)
    elif job["provider"] == "hunyuan3d":
        return _import_hunyuan3d_result(job, name, target_size)
    else:
        raise ValueError(f"Unknown provider: {job['provider']}")

def _dispatch_hyper3d_job(job: Dict[str, Any]):
    """Dispatch job to Hyper3D"""
    # Implementation would call Hyper3D API
    # For now, mark as running
    job["status"] = "running"
    job["updated_at"] = datetime.utcnow().isoformat()

def _dispatch_hunyuan3d_job(job: Dict[str, Any]):
    """Dispatch job to Hunyuan3D"""
    # Implementation would call Hunyuan3D API
    job["status"] = "running"
    job["updated_at"] = datetime.utcnow().isoformat()

def _update_job_status(job: Dict[str, Any]):
    """Poll provider for job status update"""
    # Implementation would check with provider
    pass

def _import_hyper3d_result(job: Dict[str, Any], name: str, target_size: Optional[float]) -> Dict[str, Any]:
    """Import Hyper3D result"""
    # Implementation would import the generated model
    return {
        "job_id": job["id"],
        "name": name,
        "imported": True,
    }

def _import_hunyuan3d_result(job: Dict[str, Any], name: str, target_size: Optional[float]) -> Dict[str, Any]:
    """Import Hunyuan3D result"""
    # Implementation would import the generated model
    return {
        "job_id": job["id"],
        "name": name,
        "imported": True,
    }
```

**Step 2: Update addon.py to include job handlers**

```python
# In addon.py, add to imports
from .handlers.jobs import create_job, get_job, import_job_result

# In BlenderMCPServer._dispatch_command, add:
elif command_type == "create_job":
    return create_job(params)
elif command_type == "get_job":
    return get_job(params)
elif command_type == "import_job_result":
    return import_job_result(params)
```

**Step 3: Write tests**

```python
# tests/test_jobs.py
import pytest
from blender_mcp_addon.handlers.jobs import create_job, get_job, import_job_result

class TestJobManagement:
    def test_create_job(self):
        result = create_job({
            "provider": "hyper3d",
            "payload": {"text_prompt": "A red car"}
        })
        
        assert "job_id" in result
        assert result["provider"] == "hyper3d"
        assert result["status"] == "pending"
    
    def test_get_job(self):
        # Create a job first
        created = create_job({
            "provider": "hyper3d",
            "payload": {"text_prompt": "A red car"}
        })
        
        # Get the job
        result = get_job({"job_id": created["job_id"]})
        
        assert result["job_id"] == created["job_id"]
        assert "status" in result
    
    def test_get_nonexistent_job(self):
        with pytest.raises(ValueError) as exc_info:
            get_job({"job_id": "job_nonexistent"})
        assert "not found" in str(exc_info.value)
```

**Step 4: Commit**

```bash
git add blender_mcp_addon/handlers/jobs.py tests/test_jobs.py
git add addon.py  # if modified
git commit -m "feat: implement unified job management handlers"
```

---

### Task 3.2: Implement Tripo3D Integration

**Files:**
- Create: `blender_mcp_addon/handlers/assets_tripo3d.py`
- Create: `src/blender_mcp/tools/tripo3d.py`
- Modify: `src/blender_mcp/tools/__init__.py`

**Step 1: Create Tripo3D handlers in addon**

```python
# blender_mcp_addon/handlers/assets_tripo3d.py
import bpy
import requests
import json
from typing import Dict, Any, Optional
from ..api_config import APIManager

def get_tripo3d_status() -> Dict[str, Any]:
    """Get Tripo3D integration status"""
    config = APIManager.get_tripo3d_config()
    return {
        "enabled": config["enabled"],
        "has_api_key": config["api_key"] is not None,
        "message": "Tripo3D ready" if config["enabled"] else "Tripo3D disabled",
    }

def generate_tripo3d_model(params: Dict[str, Any]) -> Dict[str, Any]:
    """Generate 3D model using Tripo3D"""
    config = APIManager.get_tripo3d_config()
    
    if not config["enabled"]:
        raise ValueError("Tripo3D is not enabled")
    
    if not config["api_key"]:
        raise ValueError("Tripo3D API key not configured")
    
    text_prompt = params.get("text_prompt")
    image_url = params.get("image_url")
    
    if not text_prompt and not image_url:
        raise ValueError("Either text_prompt or image_url must be provided")
    
    # Call Tripo3D API
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    
    if text_prompt:
        payload = {"prompt": text_prompt}
        response = requests.post(
            f"{config['base_url']}/text-to-3d",
            headers=headers,
            json=payload,
            timeout=30
        )
    else:
        payload = {"image_url": image_url}
        response = requests.post(
            f"{config['base_url']}/image-to-3d",
            headers=headers,
            json=payload,
            timeout=30
        )
    
    response.raise_for_status()
    data = response.json()
    
    return {
        "task_id": data.get("task_id"),
        "status": "pending",
        "message": "Generation task created"
    }

def poll_tripo3d_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """Check Tripo3D generation status"""
    config = APIManager.get_tripo3d_config()
    task_id = params.get("task_id")
    
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    response = requests.get(
        f"{config['base_url']}/tasks/{task_id}",
        headers=headers,
        timeout=10
    )
    response.raise_for_status()
    
    data = response.json()
    
    return {
        "task_id": task_id,
        "status": data.get("status"),
        "progress": data.get("progress", 0),
        "model_url": data.get("model_url"),
    }

def import_tripo3d_model(params: Dict[str, Any]) -> Dict[str, Any]:
    """Import Tripo3D generated model"""
    model_url = params.get("model_url")
    name = params.get("name", "Tripo3D_Model")
    
    if not model_url:
        raise ValueError("model_url is required")
    
    # Download and import model
    import tempfile
    import os
    
    temp_dir = tempfile.gettempdir()
    model_path = os.path.join(temp_dir, f"{name}.glb")
    
    response = requests.get(model_url, timeout=60)
    response.raise_for_status()
    
    with open(model_path, "wb") as f:
        f.write(response.content)
    
    # Import into Blender
    bpy.ops.import_scene.gltf(filepath=model_path)
    
    # Rename imported object
    imported = bpy.context.selected_objects
    if imported:
        for obj in imported:
            obj.name = name
    
    return {
        "name": name,
        "imported_objects": [obj.name for obj in imported],
        "status": "success"
    }
```

**Step 2: Create Tripo3D MCP tools**

```python
# src/blender_mcp/tools/tripo3d.py
import json
import logging
from typing import Any, Dict, Optional, List

from mcp.server.fastmcp import Context

from ..server import get_blender_connection, mcp
from ..telemetry_decorator import telemetry_tool
from ..schemas import SuccessResponse, ErrorResponse

logger = logging.getLogger("BlenderMCPTools")

@telemetry_tool("get_tripo3d_status")
@mcp.tool()
async def get_tripo3d_status(ctx: Context) -> str:
    """Check Tripo3D integration status."""
    try:
        blender = get_blender_connection()
        result = blender.send_command("get_tripo3d_status", {})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting Tripo3D status: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("generate_tripo3d_model")
@mcp.tool()
async def generate_tripo3d_model(
    ctx: Context,
    text_prompt: Optional[str] = None,
    image_url: Optional[str] = None,
) -> str:
    """
    Generate 3D model using Tripo3D.
    
    Parameters:
    - text_prompt: Text description of the desired model
    - image_url: URL to reference image
    
    Returns:
    - JSON string with task information
    """
    try:
        if not text_prompt and not image_url:
            return json.dumps({"error": "Either text_prompt or image_url must be provided"})
        
        blender = get_blender_connection()
        params = {}
        if text_prompt:
            params["text_prompt"] = text_prompt
        if image_url:
            params["image_url"] = image_url
        
        result = blender.send_command("generate_tripo3d_model", params)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error generating Tripo3D model: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("poll_tripo3d_status")
@mcp.tool()
async def poll_tripo3d_status(ctx: Context, task_id: str) -> str:
    """
    Check Tripo3D generation task status.
    
    Parameters:
    - task_id: Task ID from generate_tripo3d_model
    
    Returns:
    - JSON string with task status
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("poll_tripo3d_status", {"task_id": task_id})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error polling Tripo3D status: {str(e)}")
        return json.dumps({"error": str(e)})

@telemetry_tool("import_tripo3d_model")
@mcp.tool()
async def import_tripo3d_model(
    ctx: Context,
    model_url: str,
    name: str = "Tripo3D_Model",
) -> str:
    """
    Import Tripo3D generated model.
    
    Parameters:
    - model_url: URL to the generated model
    - name: Object name in scene
    
    Returns:
    - JSON string with import result
    """
    try:
        blender = get_blender_connection()
        result = blender.send_command("import_tripo3d_model", {
            "model_url": model_url,
            "name": name,
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error importing Tripo3D model: {str(e)}")
        return json.dumps({"error": str(e)})
```

**Step 3: Update tools __init__.py**

```python
# src/blender_mcp/tools/__init__.py
# Import all tool modules to register them
from . import observe
from . import scene_ops
from . import assets
from . import export
from . import jobs
from . import tripo3d  # Add this line
```

**Step 4: Update addon.py dispatcher**

```python
# In addon.py, add to imports
from .handlers.assets_tripo3d import (
    get_tripo3d_status,
    generate_tripo3d_model,
    poll_tripo3d_status,
    import_tripo3d_model,
)

# In _dispatch_command, add:
elif command_type == "get_tripo3d_status":
    return get_tripo3d_status()
elif command_type == "generate_tripo3d_model":
    return generate_tripo3d_model(params)
elif command_type == "poll_tripo3d_status":
    return poll_tripo3d_status(params)
elif command_type == "import_tripo3d_model":
    return import_tripo3d_model(params)
```

**Step 5: Write tests**

```python
# tests/test_tripo3d.py
import pytest
from unittest.mock import Mock, patch
from blender_mcp.tools.tripo3d import get_tripo3d_status, generate_tripo3d_model

class TestTripo3D:
    @pytest.mark.asyncio
    async def test_get_tripo3d_status(self, mock_blender_connection):
        mock_blender_connection.send_command.return_value = {
            "enabled": True,
            "has_api_key": True,
            "message": "Tripo3D ready"
        }
        
        with patch('blender_mcp.tools.tripo3d.get_blender_connection', return_value=mock_blender_connection):
            result = await get_tripo3d_status(None)
            data = json.loads(result)
            assert data["enabled"] is True
```

**Step 6: Commit**

```bash
git add blender_mcp_addon/handlers/assets_tripo3d.py src/blender_mcp/tools/tripo3d.py
git add tests/test_tripo3d.py
git commit -m "feat: implement Tripo3D integration"
```

---

## Phase 4: Documentation & Polish

### Task 4.1: Create API Documentation

**Files:**
- Create: `docs/api/README.md`
- Create: `docs/api/tools.md`
- Create: `docs/architecture/adr-001-async-design.md`

**Step 1: Create API documentation**

```markdown
# Blender MCP API Documentation

## Overview

Blender MCP provides a comprehensive API for controlling Blender through the Model Context Protocol (MCP).

## Tool Categories

### Scene Observation
- `observe_scene` - Get detailed scene state
- `get_scene_info` - Get scene metadata
- `get_object_info` - Get specific object details
- `get_viewport_screenshot` - Capture viewport image
- `get_selection` - Get selected objects

### Scene Operations
- `create_primitive` - Create basic shapes
- `create_light` - Add lighting
- `create_camera` - Add cameras
- `set_transform` - Modify object transforms
- `select_objects` - Manage selection
- `delete_objects` - Remove objects
- `assign_material_pbr` - Apply materials

### Asset Integration
- `search_polyhaven_assets` / `download_polyhaven_asset` - PolyHaven
- `search_sketchfab_models` / `download_sketchfab_model` - Sketchfab
- `generate_hyper3d_model_via_text` / `generate_hyper3d_model_via_images` - Hyper3D
- `generate_hunyuan3d_model` - Hunyuan3D
- `generate_tripo3d_model` - Tripo3D

### Export
- `export_glb` - Export to GLB format
- `export_scene_bundle` - Export for Next.js
- `render_preview` - Render preview image

### System
- `health_check` - Get system health
- `get_metrics` - Get Prometheus metrics
- `execute_blender_code` - Run arbitrary Python

## Request/Response Format

All tools use JSON request/response format:

```json
{
  "ok": true,
  "data": { ... },
  "request_id": "uuid",
  "meta": { ... }
}
```

## Error Handling

Errors return structured error responses:

```json
{
  "ok": false,
  "error": {
    "code": "validation_error",
    "message": "Invalid parameter",
    "details": { ... }
  },
  "request_id": "uuid"
}
```
```

**Step 2: Create Architecture Decision Record**

```markdown
# ADR-001: Async-First Tool Design

## Status
Accepted

## Context
Blender MCP tools were originally implemented as synchronous functions. However, many operations (AI generation, asset downloads) are inherently asynchronous and can take significant time.

## Decision
Implement all new tools as async functions with proper async/await patterns. Provide sync bridges where necessary for backward compatibility.

## Consequences
- Better resource utilization during long-running operations
- Ability to handle concurrent requests
- Requires careful handling of Blender's single-threaded nature
- Need for proper cancellation support
```

**Step 3: Commit**

```bash
git add docs/
git commit -m "docs: add API documentation and architecture decision records"
```

---

### Task 4.2: Create Deployment Guide

**Files:**
- Create: `docs/deployment/README.md`
- Create: `docs/deployment/docker.md`
- Create: `docs/deployment/systemd.md`

**Step 1: Create deployment documentation**

```markdown
# Deployment Guide

## Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project
COPY . .

# Install dependencies
RUN uv pip install -e ".[dev]"

# Expose port
EXPOSE 9876

CMD ["python", "-m", "blender_mcp.server"]
```

## Systemd Service

```ini
[Unit]
Description=Blender MCP Server
After=network.target

[Service]
Type=simple
User=blender-mcp
WorkingDirectory=/opt/blender-mcp
ExecStart=/usr/local/bin/uvx blender-mcp
Restart=always
RestartSec=10
Environment=BLENDER_HOST=localhost
Environment=BLENDER_PORT=9876
Environment=DISABLE_TELEMETRY=false

[Install]
WantedBy=multi-user.target
```

## Environment Variables

- `BLENDER_HOST` - Blender socket host (default: localhost)
- `BLENDER_PORT` - Blender socket port (default: 9876)
- `DISABLE_TELEMETRY` - Disable telemetry (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)
```

**Step 2: Commit**

```bash
git add docs/deployment/
git commit -m "docs: add deployment guides for Docker and systemd"
```

---

## Summary

This enterprise upgrade plan transforms Blender MCP through:

1. **Testing Infrastructure** - pytest with async support, comprehensive test coverage
2. **Validation** - Pydantic schemas for all tool inputs
3. **Observability** - Structured logging, health checks, metrics
4. **Reliability** - Retry logic, circuit breakers, connection resilience
5. **Completeness** - Job management, Tripo3D integration, all tools implemented
6. **Documentation** - API docs, architecture records, deployment guides

**Estimated Timeline:** 4-6 weeks with 1-2 developers
**Success Metrics:** 80%+ test coverage, all tools validated, health endpoint responding

---

## Next Steps

1. Review this plan with stakeholders
2. Prioritize phases based on business needs
3. Set up development worktree using `using-git-worktrees` skill
4. Begin Phase 1 implementation

**Questions for Review:**
- Should we prioritize any specific phase?
- Are there additional enterprise requirements (SSO, RBAC)?
- What's the target timeline for production deployment?

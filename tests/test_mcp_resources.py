"""Tests for MCP resources."""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch

from blender_mcp.resources import ResourceRegistry


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server."""
    return Mock()


@pytest.fixture
def registry(mock_mcp):
    """Create a resource registry."""
    return ResourceRegistry(mock_mcp)


class TestResourceRegistry:
    """Test ResourceRegistry class."""
    
    def test_list_resources(self, registry):
        """Test listing resources."""
        resources = registry.list_resources()
        
        # Check that we have expected resources
        uris = {r["uri"] for r in resources}
        assert "catalog://tools" in uris
        assert "catalog://commands" in uris
        assert "scene://current" in uris
        assert "pipeline://projects" in uris
    
    def test_list_templates(self, registry):
        """Test listing resource templates."""
        templates = registry.list_templates()
        
        # Check that we have expected templates
        patterns = {t["uriTemplate"] for t in templates}
        assert "repo://tree/{path}" in patterns
        assert "scene://object/{object_name}" in patterns
        assert "pipeline://project/{project_code}" in patterns
    
    @pytest.mark.asyncio
    async def test_read_catalog_tools(self, registry):
        """Test reading tools catalog."""
        result = await registry.read_resource("catalog://tools")
        
        # Should return JSON
        data = json.loads(result)
        assert "tools" in data
        assert "count" in data
    
    @pytest.mark.asyncio
    async def test_read_catalog_protocol(self, registry):
        """Test reading protocol capabilities."""
        result = await registry.read_resource("catalog://protocol")
        
        data = json.loads(result)
        assert "protocol_version" in data
        assert "features" in data
        assert data["features"]["tools"] is True
    
    @pytest.mark.asyncio
    async def test_read_repo_tree(self, registry):
        """Test reading repo tree resource."""
        result = await registry.read_resource("repo://tree/.")
        
        data = json.loads(result)
        assert "path" in data
        assert "type" in data
        assert data["type"] == "directory"
        assert "entries" in data
    
    @pytest.mark.asyncio
    async def test_read_repo_file(self, registry):
        """Test reading repo file resource."""
        result = await registry.read_resource("repo://file/pyproject.toml")
        
        data = json.loads(result)
        assert "path" in data
        assert "type" in data
        assert data["type"] == "file"
        assert "content" in data
    
    @pytest.mark.asyncio
    async def test_read_repo_file_path_traversal(self, registry):
        """Test that path traversal is blocked."""
        result = await registry.read_resource("repo://file/../../../etc/passwd")
        
        data = json.loads(result)
        assert "error" in data
        assert "traversal" in data["error"].lower()
    
    @pytest.mark.asyncio
    async def test_read_unknown_resource(self, registry):
        """Test reading unknown resource."""
        result = await registry.read_resource("unknown://resource")
        
        data = json.loads(result)
        assert "error" in data


class TestResourceDataFunctions:
    """Test resource data functions."""
    
    def test_get_tool_catalog(self):
        """Test tool catalog generation."""
        from blender_mcp.resources import _get_tool_catalog
        
        catalog = _get_tool_catalog()
        assert "tools" in catalog
        assert "count" in catalog
        assert catalog["count"] > 0
    
    def test_get_protocol_capabilities(self):
        """Test protocol capabilities."""
        from blender_mcp.resources import _get_protocol_capabilities
        
        caps = _get_protocol_capabilities()
        assert "protocol_version" in caps
        assert "features" in caps
        assert caps["features"]["resources"] is True

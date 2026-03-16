"""Tests for MCP completions."""

import pytest
from unittest.mock import Mock, patch

from blender_mcp.completions import CompletionRegistry, complete


@pytest.fixture
def registry():
    """Create a completion registry."""
    return CompletionRegistry()


class TestCompletionRegistry:
    """Test CompletionRegistry class."""
    
    def test_get_resource_completions_project(self, registry):
        """Test getting project completions."""
        completions = registry._get_resource_completions(
            "pipeline://project/{project_code}",
            "project_code",
            None,
        )
        
        # Should return list
        assert isinstance(completions, list)
    
    def test_get_resource_completions_asset_type(self, registry):
        """Test getting asset type completions."""
        completions = registry._get_resource_completions(
            "pipeline://asset/{asset_type}/{asset_name}",
            "asset_type",
            None,
        )
        
        # Should include standard asset types
        values = {c["value"] for c in completions}
        assert "character" in values
        assert "prop" in values
        assert "environment" in values
    
    def test_get_prompt_completions(self, registry):
        """Test getting prompt completions."""
        completions = registry._get_prompt_completions(
            "asset_creation_strategy",
            "source",
            None,
        )
        
        # Should include asset sources
        values = {c["value"] for c in completions}
        assert "polyhaven" in values
        assert "sketchfab" in values
    
    def test_get_tool_completions_camera(self, registry):
        """Test getting camera tool completions."""
        completions = registry._get_tool_completions(
            "create_composition_camera",
            "composition",
            None,
        )
        
        # Should include composition types
        values = {c["value"] for c in completions}
        assert "center" in values
        assert "rule_of_thirds" in values
        assert "golden_ratio" in values


class TestCompleteFunction:
    """Test the complete convenience function."""
    
    def test_complete_with_prefix(self):
        """Test completing with a prefix filter."""
        result = complete(
            "resource",
            "pipeline://asset/{asset_type}/{asset_name}",
            "asset_type",
            "char",
        )
        
        # Should filter to matching items
        assert isinstance(result, list)

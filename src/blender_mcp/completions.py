"""
MCP Completions implementation for Blender MCP.

Provides completions for:
- Prompt arguments where values are enumerable or discoverable
- Resource template arguments
- Tool argument completion where supported
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable

from .logging_config import get_logger

logger = get_logger("BlenderMCP.Completions")

# Type alias for completion handlers
CompletionHandler = Callable[[str, str, Optional[str]], List[Dict[str, str]]]


class CompletionRegistry:
    """Registry for MCP completions."""
    
    def __init__(self):
        self._handlers: Dict[str, CompletionHandler] = {}
    
    def register_handler(self, prefix: str, handler: CompletionHandler) -> None:
        """Register a completion handler for a URI/argument prefix."""
        self._handlers[prefix] = handler
    
    def get_completions(
        self,
        ref_type: str,
        ref_key: str,
        argument_key: Optional[str],
        prefix: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Get completions for a reference.
        
        Args:
            ref_type: Type of reference (e.g., "resource", "prompt", "tool")
            ref_key: Key for the reference (e.g., resource URI, prompt name)
            argument_key: The argument being completed
            prefix: Optional prefix to filter by
            
        Returns:
            List of completion items with "value" and optional "label"
        """
        completions = []
        
        # Check for specific handler
        handler_key = f"{ref_type}:{ref_key}:{argument_key}"
        if handler_key in self._handlers:
            return self._handlers[handler_key](ref_type, ref_key, argument_key)
        
        # Resource template completions
        if ref_type == "resource":
            completions = self._get_resource_completions(ref_key, argument_key, prefix)
        
        # Prompt argument completions
        elif ref_type == "prompt":
            completions = self._get_prompt_completions(ref_key, argument_key, prefix)
        
        # Tool argument completions
        elif ref_type == "tool":
            completions = self._get_tool_completions(ref_key, argument_key, prefix)
        
        # Filter by prefix if provided
        if prefix:
            completions = [
                c for c in completions
                if prefix.lower() in c.get("value", "").lower()
            ]
        
        return completions
    
    def _get_resource_completions(
        self,
        uri: str,
        argument: Optional[str],
        prefix: Optional[str],
    ) -> List[Dict[str, str]]:
        """Get completions for resource template arguments."""
        
        # Project codes
        if "{project_code}" in uri or argument == "project_code":
            return self._get_project_completions()
        
        # Sequence codes
        if "{sequence_code}" in uri or argument == "sequence_code":
            return self._get_sequence_completions(prefix)
        
        # Shot names
        if "{shot_name}" in uri or argument == "shot_name":
            return self._get_shot_completions(prefix)
        
        # Asset types
        if "{asset_type}" in uri or argument == "asset_type":
            return self._get_asset_type_completions()
        
        # Asset names
        if "{asset_name}" in uri or argument == "asset_name":
            return self._get_asset_completions(prefix)
        
        # Object names (scene)
        if "{object_name}" in uri or argument == "object_name":
            return self._get_object_completions(prefix)
        
        return []
    
    def _get_prompt_completions(
        self,
        prompt_name: str,
        argument: Optional[str],
        prefix: Optional[str],
    ) -> List[Dict[str, str]]:
        """Get completions for prompt arguments."""
        
        # Asset creation strategy completions
        if prompt_name == "asset_creation_strategy":
            if argument == "asset_type":
                return self._get_asset_type_completions()
            if argument == "source":
                return [
                    {"value": "polyhaven", "label": "Poly Haven"},
                    {"value": "sketchfab", "label": "Sketchfab"},
                    {"value": "hyper3d", "label": "Hyper3D Rodin"},
                    {"value": "hunyuan3d", "label": "Hunyuan3D"},
                    {"value": "code", "label": "Python Code"},
                ]
        
        # Production pipeline completions
        if prompt_name == "production_pipeline_strategy":
            if argument == "shot_name":
                return self._get_shot_completions(prefix)
            if argument == "sequence":
                return self._get_sequence_completions(prefix)
            if argument == "stage":
                return [
                    {"value": "layout", "label": "Layout"},
                    {"value": "animation", "label": "Animation"},
                    {"value": "lighting", "label": "Lighting"},
                    {"value": "render", "label": "Render"},
                    {"value": "comp", "label": "Compositing"},
                ]
        
        return []
    
    def _get_tool_completions(
        self,
        tool_name: str,
        argument: Optional[str],
        prefix: Optional[str],
    ) -> List[Dict[str, str]]:
        """Get completions for tool arguments."""
        
        # Scene operations
        if tool_name in ["get_object_info", "set_transform", "assign_material"]:
            if argument == "object_name":
                return self._get_object_completions(prefix)
        
        # Material operations
        if tool_name in ["create_bsdf_material", "create_metal_material"]:
            if argument == "name":
                return [
                    {"value": "Material_001", "label": "Suggested: Material_001"},
                    {"value": "Metal_Gold", "label": "Suggested: Metal_Gold"},
                    {"value": "Plastic_Red", "label": "Suggested: Plastic_Red"},
                ]
        
        # Lighting operations
        if tool_name in ["create_area_light", "create_three_point_lighting"]:
            if argument == "light_type":
                return [
                    {"value": "AREA", "label": "Area Light"},
                    {"value": "SUN", "label": "Sun Light"},
                    {"value": "POINT", "label": "Point Light"},
                    {"value": "SPOT", "label": "Spot Light"},
                ]
        
        # Camera operations
        if tool_name in ["create_composition_camera", "set_active_camera"]:
            if argument == "composition":
                return [
                    {"value": "center", "label": "Center Composition"},
                    {"value": "rule_of_thirds", "label": "Rule of Thirds"},
                    {"value": "golden_ratio", "label": "Golden Ratio"},
                    {"value": "diagonal", "label": "Diagonal"},
                    {"value": "frame", "label": "Frame"},
                ]
        
        # Production operations
        if tool_name in ["create_shot", "setup_shot_camera", "create_shot_version"]:
            if argument == "shot_name":
                return self._get_shot_completions(prefix)
            if argument == "sequence":
                return self._get_sequence_completions(prefix)
        
        # Color operations
        if tool_name in ["set_project_color_pipeline", "get_color_pipeline"]:
            if argument == "project_code":
                return self._get_project_completions()
            if argument == "working_colorspace":
                return [
                    {"value": "ACES - ACEScg", "label": "ACEScg (Recommended)"},
                    {"value": "ACES - ACES2065-1", "label": "ACES 2065-1"},
                    {"value": "Linear", "label": "Linear"},
                    {"value": "sRGB", "label": "sRGB"},
                ]
        
        # Tracker operations
        if tool_name in ["set_tracker_adapter", "get_tracker_status"]:
            if argument == "adapter":
                return [
                    {"value": "local", "label": "Local (File-based)"},
                    {"value": "shotgrid", "label": "ShotGrid"},
                    {"value": "ayon", "label": "AYON"},
                    {"value": "ftrack", "label": "ftrack"},
                ]
        
        return []
    
    # Data source methods
    
    def _get_project_completions(self) -> List[Dict[str, str]]:
        """Get project code completions."""
        try:
            from .pipeline import get_pipeline_storage
            storage = get_pipeline_storage()
            projects = storage.list_projects()
            return [
                {"value": p.code, "label": f"{p.name} ({p.code})"}
                for p in projects
            ]
        except Exception as e:
            logger.debug(f"Error getting project completions: {e}")
            return []
    
    def _get_sequence_completions(self, prefix: Optional[str]) -> List[Dict[str, str]]:
        """Get sequence code completions."""
        try:
            from .pipeline import get_pipeline_storage
            storage = get_pipeline_storage()
            
            sequences = []
            for project in storage.list_projects():
                for seq in storage.list_sequences(project.code):
                    if prefix is None or prefix.lower() in seq.code.lower():
                        sequences.append({
                            "value": seq.code,
                            "label": f"{seq.name} ({seq.code}) - {project.code}",
                        })
            return sequences
        except Exception as e:
            logger.debug(f"Error getting sequence completions: {e}")
            return []
    
    def _get_shot_completions(self, prefix: Optional[str]) -> List[Dict[str, str]]:
        """Get shot name completions."""
        try:
            from .pipeline import get_pipeline_storage
            storage = get_pipeline_storage()
            
            shots = []
            for project in storage.list_projects():
                for shot in storage.list_shots(project.code):
                    if prefix is None or prefix.lower() in shot.name.lower():
                        shots.append({
                            "value": shot.name,
                            "label": f"{shot.name} ({shot.sequence_code}) - {project.code}",
                        })
            return shots
        except Exception as e:
            logger.debug(f"Error getting shot completions: {e}")
            return []
    
    def _get_asset_type_completions(self) -> List[Dict[str, str]]:
        """Get asset type completions."""
        from .pipeline.entities import AssetType
        return [
            {"value": t.value, "label": t.value.capitalize()}
            for t in AssetType
        ]
    
    def _get_asset_completions(self, prefix: Optional[str]) -> List[Dict[str, str]]:
        """Get asset name completions."""
        try:
            from .pipeline import get_pipeline_storage
            storage = get_pipeline_storage()
            
            assets = []
            for project in storage.list_projects():
                for asset in storage.list_assets(project.code):
                    if prefix is None or prefix.lower() in asset.name.lower():
                        assets.append({
                            "value": asset.name,
                            "label": f"{asset.name} ({asset.asset_type.value}) - {project.code}",
                        })
            return assets
        except Exception as e:
            logger.debug(f"Error getting asset completions: {e}")
            return []
    
    def _get_object_completions(self, prefix: Optional[str]) -> List[Dict[str, str]]:
        """Get scene object name completions."""
        try:
            from .core.connection import get_blender_connection
            blender = get_blender_connection()
            result = blender.send_command("get_scene_info", {})
            
            objects = []
            for obj in result.get("objects", []):
                name = obj.get("name", "")
                if prefix is None or prefix.lower() in name.lower():
                    objects.append({
                        "value": name,
                        "label": f"{name} ({obj.get('type', 'unknown')})",
                    })
            return objects
        except Exception as e:
            logger.debug(f"Error getting object completions: {e}")
            return []


# Global registry instance
_completion_registry: Optional[CompletionRegistry] = None


def get_completion_registry() -> CompletionRegistry:
    """Get the global completion registry."""
    global _completion_registry
    if _completion_registry is None:
        _completion_registry = CompletionRegistry()
    return _completion_registry


def complete(
    ref_type: str,
    ref_key: str,
    argument_key: Optional[str] = None,
    prefix: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Convenience function to get completions.
    
    Args:
        ref_type: Type of reference (resource, prompt, tool)
        ref_key: Key for the reference
        argument_key: The argument being completed
        prefix: Optional prefix to filter by
        
    Returns:
        List of completion items
    """
    registry = get_completion_registry()
    return registry.get_completions(ref_type, ref_key, argument_key, prefix)

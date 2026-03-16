"""
OCIO / ACES color pipeline scaffolding for Blender MCP Studio.

Provides color pipeline configuration, validation, and management.
Works with or without actual OCIO library installed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .entities import ColorPipelineConfig
from .storage import PipelineStorage, get_pipeline_storage


@dataclass
class ColorspaceInfo:
    """Information about a colorspace."""
    name: str
    family: str
    description: str
    is_data: bool = False


@dataclass
class DisplayViewInfo:
    """Information about a display/view combination."""
    display: str
    view: str
    colorspace: str
    looks: List[str]


class ColorPipelineAdapter:
    """
    Adapter for color pipeline operations.
    
    Provides OCIO/ACES functionality that works both with and without
    the actual OCIO library installed.
    """
    
    # Standard ACES 1.3 colorspaces
    ACES_COLORSPACES = [
        "ACES - ACES2065-1",
        "ACES - ACEScg",
        "ACES - ACEScc",
        "ACES - ACEScct",
        "ACES - ACESproxy",
    ]
    
    # Standard utility colorspaces
    UTILITY_COLORSPACES = [
        "Utility - Raw",
        "Utility - sRGB - Texture",
        "Utility - sRGB - AP0",
        "Utility - sRGB - AP1",
        "Utility - Linear - sRGB",
        "Utility - Linear - Rec.709",
        "Utility - Linear - Rec.2020",
        "Utility - Gamma 1.8 - Rec.709",
        "Utility - Gamma 2.2 - Rec.709",
        "Utility - Gamma 2.4 - Rec.709",
    ]
    
    # Standard displays and views
    STANDARD_DISPLAYS = ["ACES", "sRGB", "Rec.709", "P3-DCI", "Rec.2020"]
    STANDARD_VIEWS = ["sRGB", "DCDM", "P3-D60", "P3-DCI", "Rec.709"]
    
    def __init__(self, storage: Optional[PipelineStorage] = None):
        self.storage = storage or get_pipeline_storage()
        self._ocio_available = self._check_ocio_available()
    
    def _check_ocio_available(self) -> bool:
        """Check if the OCIO library is available."""
        try:
            import PyOpenColorIO as OCIO
            return True
        except ImportError:
            return False
    
    @property
    def ocio_available(self) -> bool:
        """Whether the OCIO library is available for full operations."""
        return self._ocio_available
    
    def get_color_pipeline(self, project_code: str) -> ColorPipelineConfig:
        """
        Get the color pipeline configuration for a project.
        
        If no configuration exists, returns a default ACES configuration.
        """
        config = self.storage.get_color_config(project_code)
        if config:
            return config
        
        # Return default config
        return ColorPipelineConfig(
            project_code=project_code,
            ocio_config_path=None,
            ocio_config_name="ACES 1.3",
            working_colorspace="ACES - ACEScg",
            render_colorspace="ACES - ACEScg",
            display_colorspace="ACES - sRGB",
            texture_colorspace="Utility - sRGB - Texture",
            default_display="ACES",
            default_view="sRGB",
        )
    
    def set_project_color_pipeline(
        self,
        project_code: str,
        ocio_config_path: Optional[str] = None,
        working_colorspace: Optional[str] = None,
        render_colorspace: Optional[str] = None,
        display_colorspace: Optional[str] = None,
        texture_colorspace: Optional[str] = None,
        default_display: Optional[str] = None,
        default_view: Optional[str] = None,
    ) -> ColorPipelineConfig:
        """
        Set the color pipeline configuration for a project.
        """
        # Get existing or create new
        config = self.storage.get_color_config(project_code)
        if not config:
            config = ColorPipelineConfig(project_code=project_code)
        
        # Update fields
        if ocio_config_path is not None:
            config.ocio_config_path = ocio_config_path
        if working_colorspace is not None:
            config.working_colorspace = working_colorspace
        if render_colorspace is not None:
            config.render_colorspace = render_colorspace
        if display_colorspace is not None:
            config.display_colorspace = display_colorspace
        if texture_colorspace is not None:
            config.texture_colorspace = texture_colorspace
        if default_display is not None:
            config.default_display = default_display
        if default_view is not None:
            config.default_view = default_view
        
        # Save
        self.storage.set_color_config(config)
        return config
    
    def validate_color_pipeline(self, project_code: str) -> Dict[str, Any]:
        """
        Validate the color pipeline configuration.
        
        Returns a validation report with any issues found.
        """
        config = self.get_color_pipeline(project_code)
        issues = []
        warnings = []
        
        # Check OCIO config path if specified
        if config.ocio_config_path:
            if not Path(config.ocio_config_path).exists():
                issues.append(f"OCIO config path does not exist: {config.ocio_config_path}")
        
        # Validate colorspaces
        valid_colorspaces = self.ACES_COLORSPACES + self.UTILITY_COLORSPACES
        
        if config.working_colorspace not in valid_colorspaces:
            warnings.append(f"Working colorspace may not be standard: {config.working_colorspace}")
        
        if config.render_colorspace not in valid_colorspaces:
            warnings.append(f"Render colorspace may not be standard: {config.render_colorspace}")
        
        # Validate display/view
        if config.default_display not in self.STANDARD_DISPLAYS:
            warnings.append(f"Display may not be standard: {config.default_display}")
        
        if config.default_view not in self.STANDARD_VIEWS:
            warnings.append(f"View may not be standard: {config.default_view}")
        
        # If OCIO is available, do deeper validation
        if self._ocio_available and config.ocio_config_path:
            try:
                import PyOpenColorIO as OCIO
                ocio_config = OCIO.Config.CreateFromFile(config.ocio_config_path)
                
                # Check colorspaces exist in config
                for cs in [config.working_colorspace, config.render_colorspace]:
                    if not ocio_config.getColorSpace(cs):
                        issues.append(f"Colorspace not found in OCIO config: {cs}")
                
            except Exception as e:
                issues.append(f"Error loading OCIO config: {e}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "config": config.model_dump(),
        }
    
    def get_available_colorspaces(self) -> List[str]:
        """Get list of available colorspaces."""
        return self.ACES_COLORSPACES + self.UTILITY_COLORSPACES
    
    def get_available_displays(self) -> List[str]:
        """Get list of available displays."""
        return self.STANDARD_DISPLAYS
    
    def get_available_views(self, display: Optional[str] = None) -> List[str]:
        """Get list of available views, optionally filtered by display."""
        # For now, return all views
        # In a full implementation, this would query the OCIO config
        return self.STANDARD_VIEWS
    
    def get_ocio_views(self, project_code: str) -> Dict[str, List[str]]:
        """
        Get available display/view combinations.
        
        Returns a dictionary mapping display names to lists of views.
        """
        config = self.get_color_pipeline(project_code)
        
        if self._ocio_available and config.ocio_config_path:
            try:
                import PyOpenColorIO as OCIO
                ocio_config = OCIO.Config.CreateFromFile(config.ocio_config_path)
                
                result = {}
                for display in ocio_config.getDisplays():
                    result[display] = list(ocio_config.getViews(display))
                return result
                
            except Exception as e:
                # Fall back to defaults
                pass
        
        # Return default display/views
        return {
            "ACES": ["sRGB", "DCDM", "P3-D60"],
            "sRGB": ["sRGB"],
            "Rec.709": ["Rec.709"],
        }
    
    def tag_texture_colorspace(
        self,
        texture_path: str,
        colorspace: str,
        project_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Determine the appropriate colorspace for a texture.
        
        Returns metadata about the texture's colorspace assignment.
        """
        # Default to sRGB texture colorspace
        if project_code:
            config = self.get_color_pipeline(project_code)
            texture_colorspace = config.texture_colorspace
        else:
            texture_colorspace = "Utility - sRGB - Texture"
        
        # Auto-detect based on file naming conventions
        path_lower = texture_path.lower()
        if any(suffix in path_lower for suffix in ["_raw", "_linear", ".exr", ".hdr"]):
            texture_colorspace = "Utility - Raw"
        elif any(suffix in path_lower for suffix in ["_acescg", "_aces"]):
            texture_colorspace = "ACES - ACEScg"
        elif colorspace:
            texture_colorspace = colorspace
        
        return {
            "texture_path": texture_path,
            "colorspace": texture_colorspace,
            "auto_detected": colorspace is None,
            "project_code": project_code,
        }
    
    def prepare_aces_render_outputs(
        self,
        project_code: str,
        output_paths: List[str],
        file_format: str = "EXR",
    ) -> Dict[str, Any]:
        """
        Prepare render output configuration for ACES workflow.
        
        Returns configuration for render outputs with proper colorspace handling.
        """
        config = self.get_color_pipeline(project_code)
        
        # Determine datatype based on format
        if file_format.upper() == "EXR":
            datatype = config.exr_datatype
            compression = config.exr_compression
        else:
            datatype = "uint8"
            compression = "none"
        
        outputs = []
        for path in output_paths:
            outputs.append({
                "path": path,
                "format": file_format,
                "colorspace": config.render_colorspace,
                "datatype": datatype,
                "compression": compression,
            })
        
        return {
            "project_code": project_code,
            "render_colorspace": config.render_colorspace,
            "display_colorspace": config.display_colorspace,
            "outputs": outputs,
            "recommendations": [
                f"Render to {config.render_colorspace}",
                f"View with {config.default_display}/{config.default_view}",
                "Use half-float EXR for HDR preservation",
            ],
        }
    
    def create_ocio_config_template(self, output_path: str, project_name: str) -> str:
        """
        Create a basic OCIO config template file.
        
        This creates a minimal OCIO config that can be extended.
        """
        config_content = f"""ocio_profile_version: 2

search_path: luts
strictparsing: true
luma: [0.2126, 0.7152, 0.0722]

roles:
  default: ACES - ACEScg
  scene_linear: ACES - ACEScg
  data: Utility - Raw
  color_picking: Utility - sRGB - Texture
  texture_paint: Utility - sRGB - Texture
  matte_paint: Utility - sRGB - Texture
  rendering: ACES - ACEScg
  compositing_linear: ACES - ACEScg

file_rules:
  - !<Rule> {{name: Default, colorspace: ACES - ACEScg}}

displays:
  ACES:
    - !<View> {{name: sRGB, colorspace: Output - sRGB}}
    - !<View> {{name: DCDM, colorspace: Output - DCDM}}
    - !<View> {{name: P3-D60, colorspace: Output - P3-D60}}
  sRGB:
    - !<View> {{name: sRGB, colorspace: Utility - sRGB - Texture}}

active_displays: [ACES, sRGB]
active_views: [sRGB, DCDM, P3-D60]

colorspaces:
  - !<ColorSpace>
    name: ACES - ACEScg
    family: ACES
    equalitygroup: ""
    bitdepth: 32f
    description: |
      ACEScg working space
    isdata: false
    allocation: uniform
    allocationvars: [-8, 5, 0.00390625]
    to_reference: !<MatrixTransform> {{
      matrix: [0.6954522414, 0.1406786964, 0.1638690622, 0, 
               0.0447945634, 0.8596711185, 0.0955343182, 0, 
               -0.0055258826, 0.0040252103, 1.0015006723, 0, 
               0, 0, 0, 1]
    }}

  - !<ColorSpace>
    name: Utility - Raw
    family: Utility
    equalitygroup: ""
    bitdepth: 32f
    description: |
      Raw data (no transform)
    isdata: true
    allocation: uniform
    to_reference: !<MatrixTransform> {{matrix: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]}}

  - !<ColorSpace>
    name: Utility - sRGB - Texture
    family: Utility
    equalitygroup: ""
    bitdepth: 8ui
    description: |
      sRGB texture colorspace
    isdata: false
    allocation: uniform
    from_reference: !<GroupTransform>
      children:
        - !<MatrixTransform> {{
          matrix: [1.025824, -0.020538, -0.005286, 0,
                   -0.012235, 1.004586, 0.007649, 0,
                   0.006827, -0.001683, 0.994856, 0,
                   0, 0, 0, 1]
        }}
        - !<ExponentWithLinearTransform> {{gamma: 2.4, offset: 0.055, direction: inverse}}
"""
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            f.write(config_content)
        
        return str(output_file)


# Global color pipeline adapter instance
_color_adapter: Optional[ColorPipelineAdapter] = None


def get_color_adapter(storage: Optional[PipelineStorage] = None) -> ColorPipelineAdapter:
    """Get the global color pipeline adapter instance."""
    global _color_adapter
    if _color_adapter is None:
        _color_adapter = ColorPipelineAdapter(storage)
    return _color_adapter

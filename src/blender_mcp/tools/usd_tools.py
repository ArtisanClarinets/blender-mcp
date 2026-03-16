"""
USD tools for Blender MCP.

Provides tools for USD package management and export.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..mcp_compat import Context
from ..server import mcp
from ..telemetry_decorator import telemetry_tool
from ..pipeline.usd import get_usd_adapter
from ..pipeline import get_pipeline_storage

logger = logging.getLogger("BlenderMCPTools")


@telemetry_tool("build_usd_asset_manifest")
@mcp.tool()
async def build_usd_asset_manifest(
    ctx: Context,
    asset_id: str,
    asset_name: str,
    asset_type: str,
    version: int = 1,
    geometry_files: Optional[List[str]] = None,
    material_files: Optional[List[str]] = None,
) -> str:
    """
    Build a USD asset manifest.
    
    Parameters:
    - asset_id: Asset ID
    - asset_name: Asset name
    - asset_type: Asset type
    - version: Version number
    - geometry_files: List of geometry file paths
    - material_files: List of material file paths
    
    Returns:
    - JSON string with asset manifest
    """
    try:
        adapter = get_usd_adapter()
        
        manifest = adapter.build_asset_manifest(
            asset_id=asset_id,
            asset_name=asset_name,
            asset_type=asset_type,
            version=version,
            geometry_paths=geometry_files,
            material_paths=material_files,
        )
        
        return json.dumps({
            "success": True,
            "manifest": manifest,
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error building asset manifest: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("build_usd_shot_manifest")
@mcp.tool()
async def build_usd_shot_manifest(
    ctx: Context,
    shot_id: str,
    shot_name: str,
    sequence_code: str,
    version: int = 1,
    frame_start: int = 1001,
    frame_end: int = 1100,
    camera_file: Optional[str] = None,
    asset_packages: Optional[List[str]] = None,
) -> str:
    """
    Build a USD shot manifest.
    
    Parameters:
    - shot_id: Shot ID
    - shot_name: Shot name
    - sequence_code: Sequence code
    - version: Version number
    - frame_start: Start frame
    - frame_end: End frame
    - camera_file: Camera file path
    - asset_packages: List of USD package IDs for referenced assets
    
    Returns:
    - JSON string with shot manifest
    """
    try:
        adapter = get_usd_adapter()
        
        manifest = adapter.build_shot_manifest(
            shot_id=shot_id,
            shot_name=shot_name,
            sequence_code=sequence_code,
            version=version,
            frame_range=(frame_start, frame_end),
            camera_path=camera_file,
            asset_references=[{"package_id": pid} for pid in (asset_packages or [])],
        )
        
        return json.dumps({
            "success": True,
            "manifest": manifest,
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error building shot manifest: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("list_usd_variants")
@mcp.tool()
async def list_usd_variants(ctx: Context, package_id: str) -> str:
    """
    List variants for a USD package.
    
    Parameters:
    - package_id: USD package ID
    
    Returns:
    - JSON string with variant list
    """
    try:
        adapter = get_usd_adapter()
        variants = adapter.list_variants(package_id)
        
        return json.dumps({
            "success": True,
            "package_id": package_id,
            "variants": [v.model_dump() for v in variants],
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error listing variants: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("set_usd_variant_selection")
@mcp.tool()
async def set_usd_variant_selection(
    ctx: Context,
    package_id: str,
    variant_set: str,
    variant_selection: str,
) -> str:
    """
    Set the variant selection for a variant set.
    
    Parameters:
    - package_id: USD package ID
    - variant_set: Variant set name
    - variant_selection: Selected variant
    
    Returns:
    - JSON string with updated package
    """
    try:
        adapter = get_usd_adapter()
        package = adapter.set_variant_selection(package_id, variant_set, variant_selection)
        
        return json.dumps({
            "success": True,
            "package": package.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error setting variant selection: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("export_usd_asset_package")
@mcp.tool()
async def export_usd_asset_package(
    ctx: Context,
    asset_id: str,
    asset_name: str,
    asset_type: str,
    output_dir: str,
    version: int = 1,
    geometry_files: Optional[List[str]] = None,
    material_files: Optional[List[str]] = None,
) -> str:
    """
    Export an asset as a USD package.
    
    Parameters:
    - asset_id: Asset ID
    - asset_name: Asset name
    - asset_type: Asset type
    - output_dir: Output directory
    - version: Version number
    - geometry_files: List of geometry file paths
    - material_files: List of material file paths
    
    Returns:
    - JSON string with export result
    """
    try:
        adapter = get_usd_adapter()
        
        package = adapter.export_asset_package(
            asset_id=asset_id,
            asset_name=asset_name,
            asset_type=asset_type,
            output_dir=output_dir,
            version=version,
            geometry_files=geometry_files,
            material_files=material_files,
        )
        
        return json.dumps({
            "success": True,
            "package": package.model_dump(),
            "output_dir": output_dir,
            "note": "Placeholder USD files created. Full USD support requires pxr.Usd library.",
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error exporting asset package: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("export_usd_shot_package")
@mcp.tool()
async def export_usd_shot_package(
    ctx: Context,
    shot_id: str,
    shot_name: str,
    sequence_code: str,
    output_dir: str,
    version: int = 1,
    frame_start: int = 1001,
    frame_end: int = 1100,
    camera_file: Optional[str] = None,
    asset_packages: Optional[List[str]] = None,
) -> str:
    """
    Export a shot as a USD package.
    
    Parameters:
    - shot_id: Shot ID
    - shot_name: Shot name
    - sequence_code: Sequence code
    - output_dir: Output directory
    - version: Version number
    - frame_start: Start frame
    - frame_end: End frame
    - camera_file: Camera file path
    - asset_packages: List of USD package IDs for referenced assets
    
    Returns:
    - JSON string with export result
    """
    try:
        adapter = get_usd_adapter()
        
        package = adapter.export_shot_package(
            shot_id=shot_id,
            shot_name=shot_name,
            sequence_code=sequence_code,
            output_dir=output_dir,
            version=version,
            frame_range=(frame_start, frame_end),
            camera_file=camera_file,
            asset_packages=asset_packages,
        )
        
        return json.dumps({
            "success": True,
            "package": package.model_dump(),
            "output_dir": output_dir,
            "note": "Placeholder USD files created. Full USD support requires pxr.Usd library.",
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error exporting shot package: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_usd_package")
@mcp.tool()
async def get_usd_package(ctx: Context, package_id: str) -> str:
    """
    Get a USD package by ID.
    
    Parameters:
    - package_id: USD package ID
    
    Returns:
    - JSON string with package details
    """
    try:
        storage = get_pipeline_storage()
        package = storage.get_usd_package(package_id)
        
        if not package:
            return json.dumps({"error": f"USD package not found: {package_id}"})
        
        return json.dumps({
            "success": True,
            "package": package.model_dump(),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error getting USD package: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("list_usd_packages")
@mcp.tool()
async def list_usd_packages(
    ctx: Context,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
) -> str:
    """
    List USD packages.
    
    Parameters:
    - entity_type: Optional entity type filter
    - entity_id: Optional entity ID filter
    
    Returns:
    - JSON string with package list
    """
    try:
        storage = get_pipeline_storage()
        packages = storage.list_usd_packages(entity_type, entity_id)
        
        return json.dumps({
            "success": True,
            "packages": [p.model_dump() for p in packages],
            "count": len(packages),
        }, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error listing USD packages: {e}")
        return json.dumps({"error": str(e)})


@telemetry_tool("get_usd_status")
@mcp.tool()
async def get_usd_status(ctx: Context) -> str:
    """
    Get USD system status.
    
    Returns:
    - JSON string with USD status
    """
    try:
        adapter = get_usd_adapter()
        
        return json.dumps({
            "success": True,
            "usd_library_available": adapter.usd_available,
            "note": "USD scaffolding is available. Full USD support requires pxr.Usd library.",
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting USD status: {e}")
        return json.dumps({"error": str(e)})

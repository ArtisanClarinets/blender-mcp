"""
USD scaffolding for Blender MCP Studio.

Provides USD package management, manifest generation, and scaffolding
for USD-based asset and shot workflows.

Note: This module provides the data structures and manifests for USD.
Actual USD file generation requires the USD library (pxr.Usd), which
may not be available in all environments. The scaffolding is designed
to work with or without the full USD library.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .entities import USDPackage, USDLayerInfo, USDVariantInfo, generate_package_id
from .storage import PipelineStorage, get_pipeline_storage


class USDAdapter:
    """
    Adapter for USD operations.
    
    This adapter provides USD functionality that works both with and without
    the actual USD library installed. When the library is not available,
    it creates manifests and scaffolding that can be used later.
    """
    
    def __init__(self, storage: Optional[PipelineStorage] = None):
        self.storage = storage or get_pipeline_storage()
        self._usd_available = self._check_usd_available()
    
    def _check_usd_available(self) -> bool:
        """Check if the USD library is available."""
        try:
            import pxr.Usd
            return True
        except ImportError:
            return False
    
    @property
    def usd_available(self) -> bool:
        """Whether the USD library is available for full operations."""
        return self._usd_available
    
    def build_asset_manifest(
        self,
        asset_id: str,
        asset_name: str,
        asset_type: str,
        version: int,
        geometry_paths: Optional[List[str]] = None,
        material_paths: Optional[List[str]] = None,
        variants: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Build a USD asset manifest.
        
        This creates the metadata structure for a USD asset package
        without requiring the USD library.
        """
        package_id = generate_package_id("asset", asset_id, version)
        
        manifest = {
            "package_id": package_id,
            "entity_type": "asset",
            "entity_id": asset_id,
            "asset_name": asset_name,
            "asset_type": asset_type,
            "version": version,
            "usd_version": "0.23.11",
            "created_at": datetime.utcnow().isoformat(),
            "structure": {
                "root_layer": f"{asset_name}.usda",
                "sub_layers": [],
                "references": [],
            },
            "variants": variants or [],
            "geometry": {
                "paths": geometry_paths or [],
                "default_prim": f"/assets/{asset_name}",
            },
            "materials": {
                "paths": material_paths or [],
                "binding": "material_binding",
            },
            "metadata": {
                "meters_per_unit": 1.0,
                "up_axis": "Y",
                "default_prim": asset_name,
            },
        }
        
        return manifest
    
    def build_shot_manifest(
        self,
        shot_id: str,
        shot_name: str,
        sequence_code: str,
        version: int,
        frame_range: Optional[tuple[int, int]] = None,
        camera_path: Optional[str] = None,
        asset_references: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Build a USD shot manifest.
        
        This creates the metadata structure for a USD shot assembly
        without requiring the USD library.
        """
        package_id = generate_package_id("shot", shot_id, version)
        
        manifest = {
            "package_id": package_id,
            "entity_type": "shot",
            "entity_id": shot_id,
            "shot_name": shot_name,
            "sequence_code": sequence_code,
            "version": version,
            "usd_version": "0.23.11",
            "created_at": datetime.utcnow().isoformat(),
            "structure": {
                "root_layer": f"{shot_name}.usda",
                "sub_layers": [
                    {"name": "camera", "path": f"{shot_name}_camera.usda"},
                    {"name": "animation", "path": f"{shot_name}_animation.usda"},
                    {"name": "lighting", "path": f"{shot_name}_lighting.usda"},
                ],
                "references": [],
            },
            "timing": {
                "frame_start": frame_range[0] if frame_range else 1001,
                "frame_end": frame_range[1] if frame_range else 1100,
                "frame_rate": 24.0,
            },
            "camera": {
                "path": camera_path,
                "default_cam": "/camera/camera01",
            },
            "assets": asset_references or [],
            "metadata": {
                "meters_per_unit": 1.0,
                "up_axis": "Y",
                "default_prim": shot_name,
            },
        }
        
        return manifest
    
    def list_variants(self, package_id: str) -> List[USDVariantInfo]:
        """List variants for a USD package."""
        package = self.storage.get_usd_package(package_id)
        if not package:
            return []
        return package.variants
    
    def set_variant_selection(
        self,
        package_id: str,
        variant_set: str,
        variant_selection: str,
    ) -> USDPackage:
        """
        Set the variant selection for a variant set.
        
        Note: This updates the stored metadata. Actual variant authoring
        in USD files requires the USD library.
        """
        package = self.storage.get_usd_package(package_id)
        if not package:
            raise ValueError(f"USD package not found: {package_id}")
        
        # Find or create variant
        for variant in package.variants:
            if variant.name == variant_set:
                if variant_selection not in variant.selections:
                    variant.selections.append(variant_selection)
                variant.default_selection = variant_selection
                break
        else:
            # Create new variant
            package.variants.append(USDVariantInfo(
                name=variant_set,
                selections=[variant_selection],
                default_selection=variant_selection,
            ))
        
        self.storage.create_usd_package(package)
        return package
    
    def export_asset_package(
        self,
        asset_id: str,
        asset_name: str,
        asset_type: str,
        output_dir: str,
        version: int = 1,
        geometry_files: Optional[List[str]] = None,
        material_files: Optional[List[str]] = None,
    ) -> USDPackage:
        """
        Export an asset as a USD package.
        
        Creates the package structure and manifests. If USD library is
        available, also creates the actual USD files.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Build manifest
        manifest = self.build_asset_manifest(
            asset_id=asset_id,
            asset_name=asset_name,
            asset_type=asset_type,
            version=version,
            geometry_paths=geometry_files,
            material_paths=material_files,
        )
        
        # Create package record
        package_id = manifest["package_id"]
        root_layer_path = str(output_path / manifest["structure"]["root_layer"])
        
        package = USDPackage(
            package_id=package_id,
            entity_type="asset",
            entity_id=asset_id,
            root_layer_path=root_layer_path,
            layers=[],
            variants=[],
            dependencies=[],
        )
        
        # Save manifest
        manifest_path = output_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        # If USD available, create actual USD files
        if self._usd_available:
            self._create_asset_usd_files(output_path, manifest)
        else:
            # Create placeholder files
            self._create_placeholder_files(output_path, manifest)
        
        # Store package record
        self.storage.create_usd_package(package)
        
        return package
    
    def export_shot_package(
        self,
        shot_id: str,
        shot_name: str,
        sequence_code: str,
        output_dir: str,
        version: int = 1,
        frame_range: Optional[tuple[int, int]] = None,
        camera_file: Optional[str] = None,
        asset_packages: Optional[List[str]] = None,
    ) -> USDPackage:
        """
        Export a shot as a USD package.
        
        Creates the shot assembly structure and manifests.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Build references from asset packages
        asset_refs = []
        if asset_packages:
            for pkg_id in asset_packages:
                pkg = self.storage.get_usd_package(pkg_id)
                if pkg:
                    asset_refs.append({
                        "package_id": pkg_id,
                        "entity_id": pkg.entity_id,
                        "path": pkg.root_layer_path,
                    })
        
        # Build manifest
        manifest = self.build_shot_manifest(
            shot_id=shot_id,
            shot_name=shot_name,
            sequence_code=sequence_code,
            version=version,
            frame_range=frame_range,
            camera_path=camera_file,
            asset_references=asset_refs,
        )
        
        # Create package record
        package_id = manifest["package_id"]
        root_layer_path = str(output_path / manifest["structure"]["root_layer"])
        
        package = USDPackage(
            package_id=package_id,
            entity_type="shot",
            entity_id=shot_id,
            root_layer_path=root_layer_path,
            layers=[
                USDLayerInfo(
                    name=layer["name"],
                    path=str(output_path / layer["path"]),
                    layer_type="subLayer",
                )
                for layer in manifest["structure"]["sub_layers"]
            ],
            variants=[],
            dependencies=asset_packages or [],
        )
        
        # Save manifest
        manifest_path = output_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        # If USD available, create actual USD files
        if self._usd_available:
            self._create_shot_usd_files(output_path, manifest)
        else:
            # Create placeholder files
            self._create_placeholder_files(output_path, manifest)
        
        # Store package record
        self.storage.create_usd_package(package)
        
        return package
    
    def _create_asset_usd_files(self, output_path: Path, manifest: Dict[str, Any]) -> None:
        """Create actual USD files using the USD library."""
        try:
            from pxr import Usd, UsdGeom, Sdf
            
            # Create root layer
            root_path = output_path / manifest["structure"]["root_layer"]
            stage = Usd.Stage.CreateNew(str(root_path))
            
            # Set metadata
            stage.SetMetadata("metersPerUnit", manifest["metadata"]["meters_per_unit"])
            stage.SetMetadata("upAxis", manifest["metadata"]["up_axis"])
            
            # Create default prim
            asset_name = manifest["asset_name"]
            default_prim = UsdGeom.Xform.Define(stage, f"/assets/{asset_name}")
            stage.SetDefaultPrim(default_prim.GetPrim())
            
            # Save
            stage.GetRootLayer().Save()
            
        except Exception as e:
            # Fall back to placeholders
            self._create_placeholder_files(output_path, manifest)
    
    def _create_shot_usd_files(self, output_path: Path, manifest: Dict[str, Any]) -> None:
        """Create actual USD files for a shot using the USD library."""
        try:
            from pxr import Usd, UsdGeom, Sdf
            
            # Create sub-layers first
            for layer_info in manifest["structure"]["sub_layers"]:
                layer_path = output_path / layer_info["path"]
                stage = Usd.Stage.CreateNew(str(layer_path))
                
                if layer_info["name"] == "camera":
                    # Create camera
                    UsdGeom.Camera.Define(stage, "/camera/camera01")
                
                stage.GetRootLayer().Save()
            
            # Create root layer
            root_path = output_path / manifest["structure"]["root_layer"]
            stage = Usd.Stage.CreateNew(str(root_path))
            
            # Set metadata
            stage.SetMetadata("metersPerUnit", manifest["metadata"]["meters_per_unit"])
            stage.SetMetadata("upAxis", manifest["metadata"]["up_axis"])
            stage.SetMetadata("startTimeCode", manifest["timing"]["frame_start"])
            stage.SetMetadata("endTimeCode", manifest["timing"]["frame_end"])
            stage.SetMetadata("timeCodesPerSecond", manifest["timing"]["frame_rate"])
            
            # Create default prim
            shot_name = manifest["shot_name"]
            default_prim = UsdGeom.Xform.Define(stage, f"/shots/{shot_name}")
            stage.SetDefaultPrim(default_prim.GetPrim())
            
            # Add sublayers
            for layer_info in manifest["structure"]["sub_layers"]:
                layer_path = output_path / layer_info["path"]
                stage.GetRootLayer().subLayerPaths.append(str(layer_path))
            
            # Save
            stage.GetRootLayer().Save()
            
        except Exception as e:
            # Fall back to placeholders
            self._create_placeholder_files(output_path, manifest)
    
    def _create_placeholder_files(self, output_path: Path, manifest: Dict[str, Any]) -> None:
        """Create placeholder files when USD library is not available."""
        # Create root layer placeholder
        root_layer = manifest["structure"]["root_layer"]
        root_path = output_path / root_layer
        
        placeholder_content = f"""#usda 1.0
(
    doc = "USD Asset/Shot - Placeholder"
    metersPerUnit = {manifest["metadata"]["meters_per_unit"]}
    upAxis = "{manifest["metadata"]["up_axis"]}"
)

# This is a placeholder USD file
# Full USD content requires the USD library (pxr.Usd)
# Manifest: {output_path / "manifest.json"}

"""
        
        with open(root_path, "w") as f:
            f.write(placeholder_content)
        
        # Create sub-layer placeholders
        for layer_info in manifest["structure"].get("sub_layers", []):
            layer_path = output_path / layer_info["path"]
            with open(layer_path, "w") as f:
                f.write(f"""#usda 1.0
(
    doc = "USD Layer - Placeholder"
)

# Placeholder for {layer_info["name"]} layer

""")


# Global USD adapter instance
_usd_adapter: Optional[USDAdapter] = None


def get_usd_adapter(storage: Optional[PipelineStorage] = None) -> USDAdapter:
    """Get the global USD adapter instance."""
    global _usd_adapter
    if _usd_adapter is None:
        _usd_adapter = USDAdapter(storage)
    return _usd_adapter

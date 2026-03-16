"""
File-backed storage for pipeline entities.

Provides durable storage for projects, sequences, shots, assets,
publishes, and other pipeline entities using JSON files.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from datetime import datetime

from .entities import (
    Project,
    Sequence,
    Shot,
    Asset,
    Workfile,
    Publish,
    ReviewVersion,
    ColorPipelineConfig,
    USDPackage,
    TrackerSyncState,
    generate_publish_id,
    generate_package_id,
)

T = TypeVar("T")

# Default pipeline root - can be overridden via environment
DEFAULT_PIPELINE_ROOT = Path.home() / ".blender_mcp" / "pipeline"
PIPELINE_ROOT = Path(os.environ.get("BLENDER_MCP_PIPELINE_ROOT", DEFAULT_PIPELINE_ROOT))


class PipelineStorage:
    """File-backed storage for pipeline entities."""
    
    def __init__(self, root_path: Optional[Union[str, Path]] = None):
        self.root = Path(root_path) if root_path else PIPELINE_ROOT
        self.root.mkdir(parents=True, exist_ok=True)
        
        # Ensure subdirectories exist
        for subdir in ["projects", "publishes", "workfiles", "reviews", "usd", "tracker"]:
            (self.root / subdir).mkdir(exist_ok=True)
    
    def _project_path(self, project_code: str) -> Path:
        """Get the path for a project directory."""
        return self.root / "projects" / project_code
    
    def _ensure_project_dir(self, project_code: str) -> Path:
        """Ensure project directory structure exists."""
        project_path = self._project_path(project_code)
        for subdir in ["sequences", "shots", "assets", "config"]:
            (project_path / subdir).mkdir(parents=True, exist_ok=True)
        return project_path
    
    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        """Write data to a JSON file atomically."""
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        temp_path.replace(path)
    
    def _read_json(self, path: Path) -> Optional[Dict[str, Any]]:
        """Read data from a JSON file."""
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Project operations
    
    def create_project(self, project: Project) -> Project:
        """Create a new project."""
        self._ensure_project_dir(project.code)
        path = self._project_path(project.code) / "project.json"
        self._write_json(path, project.model_dump())
        return project
    
    def get_project(self, project_code: str) -> Optional[Project]:
        """Get a project by code."""
        path = self._project_path(project_code) / "project.json"
        data = self._read_json(path)
        if data:
            return Project(**data)
        return None
    
    def list_projects(self) -> List[Project]:
        """List all projects."""
        projects = []
        projects_dir = self.root / "projects"
        if projects_dir.exists():
            for project_dir in projects_dir.iterdir():
                if project_dir.is_dir():
                    project = self.get_project(project_dir.name)
                    if project:
                        projects.append(project)
        return sorted(projects, key=lambda p: p.created_at, reverse=True)
    
    def update_project(self, project: Project) -> Project:
        """Update an existing project."""
        project.updated_at = datetime.utcnow()
        path = self._project_path(project.code) / "project.json"
        self._write_json(path, project.model_dump())
        return project
    
    # Sequence operations
    
    def create_sequence(self, sequence: Sequence) -> Sequence:
        """Create a new sequence."""
        self._ensure_project_dir(sequence.project_code)
        path = self._project_path(sequence.project_code) / "sequences" / f"{sequence.code}.json"
        self._write_json(path, sequence.model_dump())
        return sequence
    
    def get_sequence(self, project_code: str, sequence_code: str) -> Optional[Sequence]:
        """Get a sequence by code."""
        path = self._project_path(project_code) / "sequences" / f"{sequence_code}.json"
        data = self._read_json(path)
        if data:
            return Sequence(**data)
        return None
    
    def list_sequences(self, project_code: str) -> List[Sequence]:
        """List all sequences in a project."""
        sequences = []
        seq_dir = self._project_path(project_code) / "sequences"
        if seq_dir.exists():
            for seq_file in seq_dir.glob("*.json"):
                data = self._read_json(seq_file)
                if data:
                    sequences.append(Sequence(**data))
        return sorted(sequences, key=lambda s: s.created_at)
    
    # Shot operations
    
    def create_shot(self, shot: Shot) -> Shot:
        """Create a new shot."""
        self._ensure_project_dir(shot.project_code)
        path = self._project_path(shot.project_code) / "shots" / f"{shot.name}.json"
        self._write_json(path, shot.model_dump())
        return shot
    
    def get_shot(self, project_code: str, shot_name: str) -> Optional[Shot]:
        """Get a shot by name."""
        path = self._project_path(project_code) / "shots" / f"{shot_name}.json"
        data = self._read_json(path)
        if data:
            return Shot(**data)
        return None
    
    def list_shots(self, project_code: str, sequence_code: Optional[str] = None) -> List[Shot]:
        """List all shots in a project, optionally filtered by sequence."""
        shots = []
        shot_dir = self._project_path(project_code) / "shots"
        if shot_dir.exists():
            for shot_file in shot_dir.glob("*.json"):
                data = self._read_json(shot_file)
                if data:
                    shot = Shot(**data)
                    if sequence_code is None or shot.sequence_code == sequence_code:
                        shots.append(shot)
        return sorted(shots, key=lambda s: (s.sequence_code, s.shot_number))
    
    def update_shot(self, shot: Shot) -> Shot:
        """Update an existing shot."""
        shot.updated_at = datetime.utcnow()
        path = self._project_path(shot.project_code) / "shots" / f"{shot.name}.json"
        self._write_json(path, shot.model_dump())
        return shot
    
    # Asset operations
    
    def create_asset(self, asset: Asset) -> Asset:
        """Create a new asset."""
        self._ensure_project_dir(asset.project_code)
        asset_dir = self._project_path(asset.project_code) / "assets" / asset.asset_type.value
        asset_dir.mkdir(parents=True, exist_ok=True)
        path = asset_dir / asset.name / "asset.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        self._write_json(path, asset.model_dump())
        return asset
    
    def get_asset(self, project_code: str, asset_type: str, asset_name: str) -> Optional[Asset]:
        """Get an asset by type and name."""
        path = self._project_path(project_code) / "assets" / asset_type / asset_name / "asset.json"
        data = self._read_json(path)
        if data:
            return Asset(**data)
        return None
    
    def list_assets(self, project_code: str, asset_type: Optional[str] = None) -> List[Asset]:
        """List all assets in a project, optionally filtered by type."""
        assets = []
        assets_dir = self._project_path(project_code) / "assets"
        if assets_dir.exists():
            if asset_type:
                type_dirs = [assets_dir / asset_type]
            else:
                type_dirs = [d for d in assets_dir.iterdir() if d.is_dir()]
            
            for type_dir in type_dirs:
                for asset_dir in type_dir.iterdir():
                    if asset_dir.is_dir():
                        data = self._read_json(asset_dir / "asset.json")
                        if data:
                            assets.append(Asset(**data))
        return sorted(assets, key=lambda a: (a.asset_type.value, a.name))
    
    def update_asset(self, asset: Asset) -> Asset:
        """Update an existing asset."""
        asset.updated_at = datetime.utcnow()
        path = self._project_path(asset.project_code) / "assets" / asset.asset_type.value / asset.name / "asset.json"
        self._write_json(path, asset.model_dump())
        return asset
    
    # Workfile operations
    
    def create_workfile(self, workfile: Workfile) -> Workfile:
        """Create a new workfile record."""
        path = self.root / "workfiles" / f"{workfile.id}.json"
        self._write_json(path, workfile.model_dump())
        return workfile
    
    def get_workfile(self, workfile_id: str) -> Optional[Workfile]:
        """Get a workfile by ID."""
        path = self.root / "workfiles" / f"{workfile_id}.json"
        data = self._read_json(path)
        if data:
            return Workfile(**data)
        return None
    
    def list_workfiles(self, entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> List[Workfile]:
        """List workfiles, optionally filtered."""
        workfiles = []
        workfiles_dir = self.root / "workfiles"
        if workfiles_dir.exists():
            for wf_file in workfiles_dir.glob("*.json"):
                data = self._read_json(wf_file)
                if data:
                    wf = Workfile(**data)
                    if entity_type and wf.entity_type != entity_type:
                        continue
                    if entity_id and wf.entity_id != entity_id:
                        continue
                    workfiles.append(wf)
        return sorted(workfiles, key=lambda w: w.created_at, reverse=True)
    
    # Publish operations
    
    def create_publish(self, publish: Publish) -> Publish:
        """Create a new publish record."""
        # Store by publish_id for easy lookup
        path = self.root / "publishes" / f"{publish.publish_id}.json"
        self._write_json(path, publish.model_dump())
        
        # Also store in entity-specific directory
        entity_dir = self.root / "publishes" / publish.entity_type / publish.entity_id
        entity_dir.mkdir(parents=True, exist_ok=True)
        version_path = entity_dir / f"v{publish.version:03d}.json"
        self._write_json(version_path, publish.model_dump())
        
        return publish
    
    def get_publish(self, publish_id: str) -> Optional[Publish]:
        """Get a publish by ID."""
        path = self.root / "publishes" / f"{publish_id}.json"
        data = self._read_json(path)
        if data:
            return Publish(**data)
        return None
    
    def get_publish_by_version(self, entity_type: str, entity_id: str, version: int) -> Optional[Publish]:
        """Get a publish by entity and version."""
        path = self.root / "publishes" / entity_type / entity_id / f"v{version:03d}.json"
        data = self._read_json(path)
        if data:
            return Publish(**data)
        return None
    
    def list_publishes(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> List[Publish]:
        """List publishes, optionally filtered."""
        publishes = []
        
        if entity_type and entity_id:
            # List from entity-specific directory
            entity_dir = self.root / "publishes" / entity_type / entity_id
            if entity_dir.exists():
                for pub_file in entity_dir.glob("v*.json"):
                    data = self._read_json(pub_file)
                    if data:
                        pub = Publish(**data)
                        if stage and pub.stage.value != stage:
                            continue
                        publishes.append(pub)
        else:
            # List all from main publishes directory
            pub_dir = self.root / "publishes"
            if pub_dir.exists():
                for pub_file in pub_dir.glob("*.json"):
                    if pub_file.is_file():
                        data = self._read_json(pub_file)
                        if data:
                            pub = Publish(**data)
                            if entity_type and pub.entity_type != entity_type:
                                continue
                            if stage and pub.stage.value != stage:
                                continue
                            publishes.append(pub)
        
        return sorted(publishes, key=lambda p: (p.entity_id, p.version))
    
    def get_latest_publish(self, entity_type: str, entity_id: str, stage: Optional[str] = None) -> Optional[Publish]:
        """Get the latest publish for an entity."""
        publishes = self.list_publishes(entity_type, entity_id, stage)
        if publishes:
            return publishes[-1]  # Highest version
        return None
    
    # Review operations
    
    def create_review_version(self, review: ReviewVersion) -> ReviewVersion:
        """Create a new review version."""
        path = self.root / "reviews" / f"{review.id}.json"
        self._write_json(path, review.model_dump())
        return review
    
    def get_review_version(self, review_id: str) -> Optional[ReviewVersion]:
        """Get a review version by ID."""
        path = self.root / "reviews" / f"{review_id}.json"
        data = self._read_json(path)
        if data:
            return ReviewVersion(**data)
        return None
    
    def list_review_versions(self, entity_type: str, entity_id: str) -> List[ReviewVersion]:
        """List review versions for an entity."""
        reviews = []
        reviews_dir = self.root / "reviews"
        if reviews_dir.exists():
            for rev_file in reviews_dir.glob("*.json"):
                data = self._read_json(rev_file)
                if data:
                    review = ReviewVersion(**data)
                    if review.entity_type == entity_type and review.entity_id == entity_id:
                        reviews.append(review)
        return sorted(reviews, key=lambda r: r.created_at)
    
    # Color pipeline operations
    
    def get_color_config(self, project_code: str) -> Optional[ColorPipelineConfig]:
        """Get color pipeline config for a project."""
        path = self._project_path(project_code) / "config" / "color_pipeline.json"
        data = self._read_json(path)
        if data:
            return ColorPipelineConfig(**data)
        return None
    
    def set_color_config(self, config: ColorPipelineConfig) -> ColorPipelineConfig:
        """Set color pipeline config for a project."""
        self._ensure_project_dir(config.project_code)
        path = self._project_path(config.project_code) / "config" / "color_pipeline.json"
        config.updated_at = datetime.utcnow()
        self._write_json(path, config.model_dump())
        return config
    
    # USD package operations
    
    def create_usd_package(self, package: USDPackage) -> USDPackage:
        """Create a new USD package record."""
        path = self.root / "usd" / f"{package.package_id}.json"
        self._write_json(path, package.model_dump())
        return package
    
    def get_usd_package(self, package_id: str) -> Optional[USDPackage]:
        """Get a USD package by ID."""
        path = self.root / "usd" / f"{package_id}.json"
        data = self._read_json(path)
        if data:
            return USDPackage(**data)
        return None
    
    def list_usd_packages(self, entity_type: Optional[str] = None, entity_id: Optional[str] = None) -> List[USDPackage]:
        """List USD packages, optionally filtered."""
        packages = []
        usd_dir = self.root / "usd"
        if usd_dir.exists():
            for pkg_file in usd_dir.glob("*.json"):
                data = self._read_json(pkg_file)
                if data:
                    pkg = USDPackage(**data)
                    if entity_type and pkg.entity_type != entity_type:
                        continue
                    if entity_id and pkg.entity_id != entity_id:
                        continue
                    packages.append(pkg)
        return sorted(packages, key=lambda p: p.created_at)
    
    # Tracker sync operations
    
    def get_tracker_sync_state(self, entity_type: str, local_id: str) -> Optional[TrackerSyncState]:
        """Get tracker sync state for an entity."""
        path = self.root / "tracker" / f"{entity_type}_{local_id}.json"
        data = self._read_json(path)
        if data:
            return TrackerSyncState(**data)
        return None
    
    def set_tracker_sync_state(self, state: TrackerSyncState) -> TrackerSyncState:
        """Set tracker sync state for an entity."""
        path = self.root / "tracker" / f"{state.entity_type}_{state.local_id}.json"
        self._write_json(path, state.model_dump())
        return state
    
    def list_tracker_sync_states(self, tracker_adapter: Optional[str] = None) -> List[TrackerSyncState]:
        """List tracker sync states, optionally filtered by adapter."""
        states = []
        tracker_dir = self.root / "tracker"
        if tracker_dir.exists():
            for state_file in tracker_dir.glob("*.json"):
                data = self._read_json(state_file)
                if data:
                    state = TrackerSyncState(**data)
                    if tracker_adapter and state.tracker_adapter != tracker_adapter:
                        continue
                    states.append(state)
        return states


# Global storage instance
_storage_instance: Optional[PipelineStorage] = None


def get_pipeline_storage(root_path: Optional[Union[str, Path]] = None) -> PipelineStorage:
    """Get the global pipeline storage instance."""
    global _storage_instance
    if _storage_instance is None or root_path is not None:
        _storage_instance = PipelineStorage(root_path)
    return _storage_instance


def reset_storage() -> None:
    """Reset the global storage instance (useful for testing)."""
    global _storage_instance
    _storage_instance = None

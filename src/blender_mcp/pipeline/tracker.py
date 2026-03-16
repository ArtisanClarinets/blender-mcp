"""
Tracker adapter scaffolding for Blender MCP Studio.

Provides a clean abstraction for production tracker integration.
Includes a local/null adapter for when no external tracker is configured.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

from .entities import TrackerSyncState, EntityStatus
from .storage import PipelineStorage, get_pipeline_storage


@dataclass
class TrackerEntity:
    """Base class for tracker entities."""
    id: str
    name: str
    status: str
    metadata: Dict[str, Any]


@dataclass
class TrackerProject(TrackerEntity):
    """Project entity from tracker."""
    code: str
    description: str


@dataclass
class TrackerSequence(TrackerEntity):
    """Sequence entity from tracker."""
    code: str
    project_id: str


@dataclass
class TrackerShot(TrackerEntity):
    """Shot entity from tracker."""
    shot_number: int
    sequence_id: str
    frame_start: int
    frame_end: int


@dataclass
class TrackerAsset(TrackerEntity):
    """Asset entity from tracker."""
    asset_type: str
    project_id: str


class TrackerAdapter(ABC):
    """
    Abstract base class for tracker adapters.
    
    Implement this class to integrate with external trackers like
    ShotGrid, AYON, OpenPype, ftrack, etc.
    """
    
    name: str = "abstract"
    
    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """Connect to the tracker."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the tracker."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the tracker."""
        pass
    
    # Project operations
    
    @abstractmethod
    def get_projects(self) -> List[TrackerProject]:
        """Get all projects from the tracker."""
        pass
    
    @abstractmethod
    def get_project(self, project_id: str) -> Optional[TrackerProject]:
        """Get a specific project from the tracker."""
        pass
    
    # Sequence operations
    
    @abstractmethod
    def get_sequences(self, project_id: str) -> List[TrackerSequence]:
        """Get all sequences for a project."""
        pass
    
    @abstractmethod
    def get_sequence(self, sequence_id: str) -> Optional[TrackerSequence]:
        """Get a specific sequence."""
        pass
    
    # Shot operations
    
    @abstractmethod
    def get_shots(self, sequence_id: str) -> List[TrackerShot]:
        """Get all shots for a sequence."""
        pass
    
    @abstractmethod
    def get_shot(self, shot_id: str) -> Optional[TrackerShot]:
        """Get a specific shot."""
        pass
    
    @abstractmethod
    def create_shot(
        self,
        sequence_id: str,
        name: str,
        shot_number: int,
        **kwargs
    ) -> Optional[TrackerShot]:
        """Create a new shot in the tracker."""
        pass
    
    @abstractmethod
    def update_shot(self, shot_id: str, **kwargs) -> bool:
        """Update a shot in the tracker."""
        pass
    
    # Asset operations
    
    @abstractmethod
    def get_assets(self, project_id: str, asset_type: Optional[str] = None) -> List[TrackerAsset]:
        """Get all assets for a project."""
        pass
    
    @abstractmethod
    def get_asset(self, asset_id: str) -> Optional[TrackerAsset]:
        """Get a specific asset."""
        pass
    
    # Publish operations
    
    @abstractmethod
    def publish_version(
        self,
        entity_id: str,
        version_number: int,
        description: str,
        files: List[Dict[str, str]],
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Publish a version to the tracker."""
        pass
    
    @abstractmethod
    def get_publishes(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all publishes for an entity."""
        pass
    
    # Sync operations
    
    @abstractmethod
    def sync_entity_status(self, entity_type: str, local_id: str, tracker_id: str) -> TrackerSyncState:
        """Sync the status of an entity with the tracker."""
        pass


class LocalTrackerAdapter(TrackerAdapter):
    """
    Local/null tracker adapter.
    
    This adapter stores all data locally and provides deterministic
    behavior when no external tracker is configured. It's also useful
    for testing and offline workflows.
    """
    
    name = "local"
    
    def __init__(self, storage: Optional[PipelineStorage] = None):
        self.storage = storage or get_pipeline_storage()
        self._connected = False
        self._projects: Dict[str, TrackerProject] = {}
        self._sequences: Dict[str, TrackerSequence] = {}
        self._shots: Dict[str, TrackerShot] = {}
        self._assets: Dict[str, TrackerAsset] = {}
    
    def connect(self, **kwargs) -> bool:
        """Connect to local storage."""
        self._connected = True
        return True
    
    def disconnect(self) -> None:
        """Disconnect from local storage."""
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected
    
    def get_projects(self) -> List[TrackerProject]:
        """Get all projects from local storage."""
        from .entities import Project
        projects = self.storage.list_projects()
        return [
            TrackerProject(
                id=p.id,
                name=p.name,
                code=p.code,
                description=p.description,
                status=p.status.value,
                metadata={
                    "created_at": p.created_at.isoformat(),
                    "tracker_adapter": p.tracker_adapter,
                },
            )
            for p in projects
        ]
    
    def get_project(self, project_id: str) -> Optional[TrackerProject]:
        """Get a specific project."""
        from .entities import Project
        project = self.storage.get_project(project_id)
        if project:
            return TrackerProject(
                id=project.id,
                name=project.name,
                code=project.code,
                description=project.description,
                status=project.status.value,
                metadata={
                    "created_at": project.created_at.isoformat(),
                    "tracker_adapter": project.tracker_adapter,
                },
            )
        return None
    
    def get_sequences(self, project_id: str) -> List[TrackerSequence]:
        """Get all sequences for a project."""
        sequences = self.storage.list_sequences(project_id)
        return [
            TrackerSequence(
                id=s.id,
                name=s.name,
                code=s.code,
                project_id=s.project_code,
                status=s.status.value,
                metadata={
                    "created_at": s.created_at.isoformat(),
                },
            )
            for s in sequences
        ]
    
    def get_sequence(self, sequence_id: str) -> Optional[TrackerSequence]:
        """Get a specific sequence."""
        # Need to search across all projects
        for project in self.storage.list_projects():
            seq = self.storage.get_sequence(project.code, sequence_id)
            if seq:
                return TrackerSequence(
                    id=seq.id,
                    name=seq.name,
                    code=seq.code,
                    project_id=seq.project_code,
                    status=seq.status.value,
                    metadata={
                        "created_at": seq.created_at.isoformat(),
                    },
                )
        return None
    
    def get_shots(self, sequence_id: str) -> List[TrackerShot]:
        """Get all shots for a sequence."""
        # Find the sequence first
        sequence = self.get_sequence(sequence_id)
        if not sequence:
            return []
        
        shots = self.storage.list_shots(sequence.project_id, sequence.code)
        return [
            TrackerShot(
                id=s.id,
                name=s.name,
                shot_number=s.shot_number,
                sequence_id=sequence_id,
                frame_start=s.frame_start,
                frame_end=s.frame_end,
                status=s.status.value,
                metadata={
                    "created_at": s.created_at.isoformat(),
                    "description": s.description,
                },
            )
            for s in shots
        ]
    
    def get_shot(self, shot_id: str) -> Optional[TrackerShot]:
        """Get a specific shot."""
        # Search across all projects and sequences
        for project in self.storage.list_projects():
            for shot in self.storage.list_shots(project.code):
                if shot.id == shot_id or shot.name == shot_id:
                    return TrackerShot(
                        id=shot.id,
                        name=shot.name,
                        shot_number=shot.shot_number,
                        sequence_id=shot.sequence_code,
                        frame_start=shot.frame_start,
                        frame_end=shot.frame_end,
                        status=shot.status.value,
                        metadata={
                            "created_at": shot.created_at.isoformat(),
                            "description": shot.description,
                        },
                    )
        return None
    
    def create_shot(
        self,
        sequence_id: str,
        name: str,
        shot_number: int,
        **kwargs
    ) -> Optional[TrackerShot]:
        """Create a new shot."""
        from .entities import Shot
        
        sequence = self.get_sequence(sequence_id)
        if not sequence:
            return None
        
        shot = Shot(
            name=name,
            shot_number=shot_number,
            project_code=sequence.project_id,
            sequence_code=sequence.code,
            description=kwargs.get("description", ""),
            frame_start=kwargs.get("frame_start", 1001),
            frame_end=kwargs.get("frame_end", 1100),
        )
        
        self.storage.create_shot(shot)
        
        return TrackerShot(
            id=shot.id,
            name=shot.name,
            shot_number=shot.shot_number,
            sequence_id=sequence_id,
            frame_start=shot.frame_start,
            frame_end=shot.frame_end,
            status=shot.status.value,
            metadata={},
        )
    
    def update_shot(self, shot_id: str, **kwargs) -> bool:
        """Update a shot."""
        # Find the shot
        for project in self.storage.list_projects():
            for shot in self.storage.list_shots(project.code):
                if shot.id == shot_id:
                    if "frame_start" in kwargs:
                        shot.frame_start = kwargs["frame_start"]
                    if "frame_end" in kwargs:
                        shot.frame_end = kwargs["frame_end"]
                    if "status" in kwargs:
                        shot.status = EntityStatus(kwargs["status"])
                    self.storage.update_shot(shot)
                    return True
        return False
    
    def get_assets(self, project_id: str, asset_type: Optional[str] = None) -> List[TrackerAsset]:
        """Get all assets for a project."""
        assets = self.storage.list_assets(project_id, asset_type)
        return [
            TrackerAsset(
                id=a.id,
                name=a.name,
                asset_type=a.asset_type.value,
                project_id=a.project_code,
                status=a.status.value,
                metadata={
                    "created_at": a.created_at.isoformat(),
                    "variants": [v.name for v in a.variants],
                },
            )
            for a in assets
        ]
    
    def get_asset(self, asset_id: str) -> Optional[TrackerAsset]:
        """Get a specific asset."""
        # Search across all projects
        for project in self.storage.list_projects():
            for asset in self.storage.list_assets(project.code):
                if asset.id == asset_id or asset.name == asset_id:
                    return TrackerAsset(
                        id=asset.id,
                        name=asset.name,
                        asset_type=asset.asset_type.value,
                        project_id=asset.project_code,
                        status=asset.status.value,
                        metadata={
                            "created_at": asset.created_at.isoformat(),
                            "variants": [v.name for v in asset.variants],
                        },
                    )
        return None
    
    def publish_version(
        self,
        entity_id: str,
        version_number: int,
        description: str,
        files: List[Dict[str, str]],
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Publish a version."""
        # This would integrate with the publish manager
        # For now, just return a placeholder
        return {
            "version_id": f"{entity_id}_v{version_number:03d}",
            "version_number": version_number,
            "description": description,
            "files": files,
            "status": "published",
        }
    
    def get_publishes(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get all publishes for an entity."""
        publishes = self.storage.list_publishes(entity_id=entity_id)
        return [
            {
                "publish_id": p.publish_id,
                "version": p.version,
                "stage": p.stage.value,
                "status": p.status.value,
                "created_at": p.created_at.isoformat(),
            }
            for p in publishes
        ]
    
    def sync_entity_status(self, entity_type: str, local_id: str, tracker_id: str) -> TrackerSyncState:
        """Sync entity status."""
        state = TrackerSyncState(
            entity_type=entity_type,
            local_id=local_id,
            tracker_id=tracker_id,
            tracker_adapter=self.name,
            last_sync_at=datetime.utcnow(),
            sync_status="synced",
        )
        self.storage.set_tracker_sync_state(state)
        return state


# Registry of available adapters
_ADAPTER_REGISTRY: Dict[str, Type[TrackerAdapter]] = {
    "local": LocalTrackerAdapter,
}


def register_adapter(name: str, adapter_class: Type[TrackerAdapter]) -> None:
    """Register a tracker adapter."""
    _ADAPTER_REGISTRY[name] = adapter_class


def get_available_adapters() -> List[str]:
    """Get list of available adapter names."""
    return list(_ADAPTER_REGISTRY.keys())


def create_adapter(
    name: str,
    storage: Optional[PipelineStorage] = None,
    **kwargs
) -> TrackerAdapter:
    """Create a tracker adapter instance."""
    if name not in _ADAPTER_REGISTRY:
        raise ValueError(f"Unknown adapter: {name}. Available: {list(_ADAPTER_REGISTRY.keys())}")
    
    adapter_class = _ADAPTER_REGISTRY[name]
    return adapter_class(storage, **kwargs)


# Global tracker adapter instance
_tracker_adapter: Optional[TrackerAdapter] = None
_current_adapter_name: str = "local"


def get_tracker_adapter(storage: Optional[PipelineStorage] = None) -> TrackerAdapter:
    """Get the global tracker adapter instance."""
    global _tracker_adapter
    if _tracker_adapter is None:
        _tracker_adapter = create_adapter(_current_adapter_name, storage)
    return _tracker_adapter


def set_tracker_adapter(name: str, storage: Optional[PipelineStorage] = None) -> TrackerAdapter:
    """Set the current tracker adapter."""
    global _tracker_adapter, _current_adapter_name
    _current_adapter_name = name
    _tracker_adapter = create_adapter(name, storage)
    return _tracker_adapter


def get_tracker_status() -> Dict[str, Any]:
    """Get the current tracker status."""
    adapter = get_tracker_adapter()
    return {
        "adapter_name": _current_adapter_name,
        "available_adapters": get_available_adapters(),
        "connected": adapter.is_connected(),
    }

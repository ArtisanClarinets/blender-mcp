"""
Publish management for Blender MCP Studio.

Provides high-level operations for creating, managing, and querying publishes.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .entities import (
    Publish,
    PublishArtifact,
    PublishStage,
    EntityStatus,
    ValidationResult,
    Workfile,
    generate_publish_id,
)
from .storage import PipelineStorage, get_pipeline_storage
from .lineage import LineageTracker, get_lineage_tracker


class PublishManager:
    """Manages publish operations for the pipeline."""
    
    def __init__(
        self,
        storage: Optional[PipelineStorage] = None,
        lineage: Optional[LineageTracker] = None,
    ):
        self.storage = storage or get_pipeline_storage()
        self.lineage = lineage or get_lineage_tracker(storage)
    
    def create_publish(
        self,
        entity_type: str,
        entity_id: str,
        stage: Union[str, PublishStage],
        source_workfile_id: Optional[str] = None,
        description: str = "",
        created_by: str = "unknown",
        artifacts: Optional[List[Dict[str, Any]]] = None,
        previews: Optional[List[Dict[str, Any]]] = None,
        parent_publish_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
    ) -> Publish:
        """
        Create a new publish for an entity.
        
        Args:
            entity_type: "shot" or "asset"
            entity_id: The entity ID
            stage: Pipeline stage (layout, animation, lighting, render, etc.)
            source_workfile_id: ID of the source workfile
            description: Publish description
            created_by: User creating the publish
            artifacts: List of artifact dicts with name, path, type
            previews: List of preview artifact dicts
            parent_publish_id: Parent publish for lineage
            dependencies: Additional dependency publish IDs
            
        Returns:
            The created Publish object
        """
        # Convert stage to enum if string
        if isinstance(stage, str):
            stage = PublishStage(stage)
        
        # Get next version number
        latest = self.storage.get_latest_publish(entity_type, entity_id)
        version = (latest.version + 1) if latest else 1
        
        # Generate publish ID
        publish_id = generate_publish_id(entity_type, entity_id, version)
        
        # Build artifacts
        publish_artifacts = []
        if artifacts:
            for art in artifacts:
                publish_artifacts.append(PublishArtifact(
                    name=art["name"],
                    path=art["path"],
                    artifact_type=art["type"],
                    file_size=art.get("size"),
                    file_hash=art.get("hash"),
                    metadata=art.get("metadata", {}),
                ))
        
        # Build previews
        publish_previews = []
        if previews:
            for prev in previews:
                publish_previews.append(PublishArtifact(
                    name=prev["name"],
                    path=prev["path"],
                    artifact_type=prev.get("type", "preview"),
                    file_size=prev.get("size"),
                    file_hash=prev.get("hash"),
                ))
        
        # Get source file info if workfile provided
        source_file_path = None
        source_scene_hash = None
        blender_version = None
        if source_workfile_id:
            workfile = self.storage.get_workfile(source_workfile_id)
            if workfile:
                source_file_path = workfile.file_path
                source_scene_hash = workfile.scene_hash
                blender_version = workfile.blender_version
        
        # Build dependencies list
        deps = list(dependencies) if dependencies else []
        if parent_publish_id and parent_publish_id not in deps:
            deps.append(parent_publish_id)
        
        # Create publish
        publish = Publish(
            id="",  # Will be generated
            publish_id=publish_id,
            entity_type=entity_type,  # type: ignore
            entity_id=entity_id,
            version=version,
            stage=stage,
            status=EntityStatus.PENDING,
            source_workfile_id=source_workfile_id,
            source_file_path=source_file_path,
            source_scene_hash=source_scene_hash,
            blender_version=blender_version,
            description=description,
            artifacts=publish_artifacts,
            previews=publish_previews,
            dependencies=deps,
            parent_publish_id=parent_publish_id,
            created_by=created_by,
        )
        
        # Save to storage
        self.storage.create_publish(publish)
        
        # Link lineage if parent specified
        if parent_publish_id:
            self.lineage.link_parent_child(parent_publish_id, publish_id)
        
        return publish
    
    def approve_publish(self, publish_id: str, notes: str = "") -> Publish:
        """Approve a pending publish."""
        publish = self.storage.get_publish(publish_id)
        if not publish:
            raise ValueError(f"Publish not found: {publish_id}")
        
        publish.status = EntityStatus.APPROVED
        if notes:
            publish.description += f"\n[Approval notes: {notes}]"
        
        self.storage.create_publish(publish)
        return publish
    
    def reject_publish(self, publish_id: str, reason: str = "") -> Publish:
        """Reject a pending publish."""
        publish = self.storage.get_publish(publish_id)
        if not publish:
            raise ValueError(f"Publish not found: {publish_id}")
        
        publish.status = EntityStatus.REJECTED
        if reason:
            publish.description += f"\n[Rejection reason: {reason}]"
        
        self.storage.create_publish(publish)
        return publish
    
    def add_validation(self, publish_id: str, validation: ValidationResult) -> Publish:
        """Add validation results to a publish."""
        publish = self.storage.get_publish(publish_id)
        if not publish:
            raise ValueError(f"Publish not found: {publish_id}")
        
        publish.validation = validation
        self.storage.create_publish(publish)
        return publish
    
    def get_publish_manifest(self, publish_id: str) -> Dict[str, Any]:
        """
        Get a complete manifest for a publish.
        
        Includes the publish data, lineage info, and all artifacts.
        """
        publish = self.storage.get_publish(publish_id)
        if not publish:
            raise ValueError(f"Publish not found: {publish_id}")
        
        # Get lineage
        lineage_path = self.lineage.get_lineage(publish_id)
        
        # Build manifest
        manifest = {
            "publish": publish.model_dump(),
            "lineage": {
                "ancestors": [n.__dict__ for n in lineage_path.nodes if n.publish_id != publish_id],
                "depth": len(lineage_path.nodes) - 1,
            },
            "artifacts": {
                "main": [a.model_dump() for a in publish.artifacts],
                "previews": [p.model_dump() for p in publish.previews],
            },
            "manifest_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        return manifest
    
    def resolve_publish(
        self,
        entity_type: str,
        entity_id: str,
        version: Optional[int] = None,
        stage: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Publish]:
        """
        Resolve a publish reference to an actual publish.
        
        Args:
            entity_type: "shot" or "asset"
            entity_id: The entity ID
            version: Specific version, or None for latest
            stage: Filter by stage
            status: Filter by status (defaults to APPROVED)
            
        Returns:
            The matching Publish, or None if not found
        """
        if version is not None:
            return self.storage.get_publish_by_version(entity_type, entity_id, version)
        
        # Get all publishes for entity
        publishes = self.storage.list_publishes(entity_type, entity_id, stage)
        
        # Filter by status (default to APPROVED)
        target_status = status or EntityStatus.APPROVED.value
        publishes = [p for p in publishes if p.status.value == target_status]
        
        # Return latest
        if publishes:
            return publishes[-1]
        return None
    
    def get_latest_approved(self, entity_type: str, entity_id: str, stage: Optional[str] = None) -> Optional[Publish]:
        """Get the latest approved publish for an entity."""
        return self.resolve_publish(entity_type, entity_id, stage=stage, status=EntityStatus.APPROVED.value)
    
    def list_publishes_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        stage: Optional[str] = None,
        include_rejected: bool = False,
    ) -> List[Publish]:
        """List all publishes for an entity."""
        publishes = self.storage.list_publishes(entity_type, entity_id, stage)
        if not include_rejected:
            publishes = [p for p in publishes if p.status != EntityStatus.REJECTED]
        return publishes
    
    def create_workfile_record(
        self,
        entity_type: str,
        entity_id: str,
        file_path: str,
        created_by: str = "unknown",
        scene_hash: Optional[str] = None,
        blender_version: Optional[str] = None,
    ) -> Workfile:
        """Create a workfile record."""
        # Get next version
        existing = self.storage.list_workfiles(entity_type, entity_id)
        version = max((w.version_number for w in existing), default=0) + 1
        
        # Calculate file hash and size
        file_hash = None
        file_size = None
        path = Path(file_path)
        if path.exists():
            file_size = path.stat().st_size
            # Simple hash - in production, use a proper hash function
            import hashlib
            file_hash = hashlib.md5(str(path.stat().st_mtime).encode()).hexdigest()
        
        workfile = Workfile(
            entity_type=entity_type,  # type: ignore
            entity_id=entity_id,
            file_path=file_path,
            file_hash=file_hash,
            file_size=file_size,
            version_number=version,
            created_by=created_by,
            scene_hash=scene_hash,
            blender_version=blender_version,
        )
        
        self.storage.create_workfile(workfile)
        return workfile
    
    def compare_publishes(self, publish_id_a: str, publish_id_b: str) -> Dict[str, Any]:
        """Compare two publishes and return differences."""
        pub_a = self.storage.get_publish(publish_id_a)
        pub_b = self.storage.get_publish(publish_id_b)
        
        if not pub_a or not pub_b:
            raise ValueError("One or both publishes not found")
        
        return {
            "publish_a": pub_a.publish_id,
            "publish_b": pub_b.publish_id,
            "version_diff": pub_b.version - pub_a.version,
            "stage_changed": pub_a.stage != pub_b.stage,
            "artifact_changes": {
                "added": [a.name for a in pub_b.artifacts if a.name not in {x.name for x in pub_a.artifacts}],
                "removed": [a.name for a in pub_a.artifacts if a.name not in {x.name for x in pub_b.artifacts}],
            },
            "same_lineage": pub_a.publish_id in [p.publish_id for p in self.lineage.get_ancestors(publish_id_b)],
        }


# Global publish manager instance
_publish_manager: Optional[PublishManager] = None


def get_publish_manager(
    storage: Optional[PipelineStorage] = None,
    lineage: Optional[LineageTracker] = None,
) -> PublishManager:
    """Get the global publish manager instance."""
    global _publish_manager
    if _publish_manager is None:
        _publish_manager = PublishManager(storage, lineage)
    return _publish_manager

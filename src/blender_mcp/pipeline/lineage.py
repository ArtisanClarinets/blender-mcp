"""
Publish lineage tracking for Blender MCP Studio.

Tracks parent-child relationships between publishes and provides
provenance tracking for pipeline entities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path

from .entities import Publish, EntityStatus
from .storage import PipelineStorage, get_pipeline_storage


@dataclass
class LineageNode:
    """A node in the lineage graph."""
    publish_id: str
    entity_type: str
    entity_id: str
    version: int
    stage: str
    status: EntityStatus
    created_at: datetime
    parent_ids: List[str] = field(default_factory=list)
    child_ids: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class LineagePath:
    """A path through the lineage graph."""
    nodes: List[LineageNode]
    
    @property
    def length(self) -> int:
        return len(self.nodes)
    
    @property
    def start_publish_id(self) -> Optional[str]:
        return self.nodes[0].publish_id if self.nodes else None
    
    @property
    def end_publish_id(self) -> Optional[str]:
        return self.nodes[-1].publish_id if self.nodes else None


class LineageTracker:
    """Tracks publish lineage and provenance."""
    
    def __init__(self, storage: Optional[PipelineStorage] = None):
        self.storage = storage or get_pipeline_storage()
    
    def _publish_to_node(self, publish: Publish) -> LineageNode:
        """Convert a Publish to a LineageNode."""
        return LineageNode(
            publish_id=publish.publish_id,
            entity_type=publish.entity_type,
            entity_id=publish.entity_id,
            version=publish.version,
            stage=publish.stage.value,
            status=publish.status,
            created_at=publish.created_at,
            parent_ids=publish.dependencies.copy() if publish.dependencies else [],
            child_ids=publish.child_publish_ids.copy() if publish.child_publish_ids else [],
            artifacts=[a.name for a in publish.artifacts],
        )
    
    def link_parent_child(self, parent_publish_id: str, child_publish_id: str) -> None:
        """
        Link a parent publish to a child publish.
        
        This establishes a lineage relationship where the child was derived
        from or depends on the parent.
        """
        parent = self.storage.get_publish(parent_publish_id)
        child = self.storage.get_publish(child_publish_id)
        
        if not parent:
            raise ValueError(f"Parent publish not found: {parent_publish_id}")
        if not child:
            raise ValueError(f"Child publish not found: {child_publish_id}")
        
        # Update parent
        if child_publish_id not in parent.child_publish_ids:
            parent.child_publish_ids.append(child_publish_id)
            self.storage.create_publish(parent)  # Re-save
        
        # Update child
        if parent_publish_id not in child.dependencies:
            child.dependencies.append(parent_publish_id)
            self.storage.create_publish(child)  # Re-save
    
    def get_lineage(self, publish_id: str, direction: str = "both", max_depth: int = 10) -> LineagePath:
        """
        Get the lineage path for a publish.
        
        Args:
            publish_id: The publish to start from
            direction: "up" (ancestors), "down" (descendants), or "both"
            max_depth: Maximum depth to traverse
            
        Returns:
            LineagePath containing the lineage nodes
        """
        visited: Set[str] = set()
        nodes: List[LineageNode] = []
        
        def traverse_up(pid: str, depth: int) -> None:
            if depth <= 0 or pid in visited:
                return
            visited.add(pid)
            
            publish = self.storage.get_publish(pid)
            if not publish:
                return
            
            node = self._publish_to_node(publish)
            nodes.insert(0, node)  # Add at beginning for up traversal
            
            for parent_id in node.parent_ids:
                traverse_up(parent_id, depth - 1)
        
        def traverse_down(pid: str, depth: int) -> None:
            if depth <= 0 or pid in visited:
                return
            visited.add(pid)
            
            publish = self.storage.get_publish(pid)
            if not publish:
                return
            
            node = self._publish_to_node(publish)
            nodes.append(node)  # Add at end for down traversal
            
            for child_id in node.child_ids:
                traverse_down(child_id, depth - 1)
        
        if direction in ("up", "both"):
            traverse_up(publish_id, max_depth)
        
        if direction in ("down", "both"):
            # Clear visited for down traversal if we already did up
            if direction == "both":
                visited.clear()
                # Re-add the starting node
                start_publish = self.storage.get_publish(publish_id)
                if start_publish:
                    nodes.append(self._publish_to_node(start_publish))
                    visited.add(publish_id)
            traverse_down(publish_id, max_depth)
        
        return LineagePath(nodes=nodes)
    
    def get_ancestors(self, publish_id: str, max_depth: int = 10) -> List[LineageNode]:
        """Get all ancestors of a publish."""
        path = self.get_lineage(publish_id, direction="up", max_depth=max_depth)
        # Exclude the starting node
        return [n for n in path.nodes if n.publish_id != publish_id]
    
    def get_descendants(self, publish_id: str, max_depth: int = 10) -> List[LineageNode]:
        """Get all descendants of a publish."""
        path = self.get_lineage(publish_id, direction="down", max_depth=max_depth)
        # Exclude the starting node
        return [n for n in path.nodes if n.publish_id != publish_id]
    
    def get_common_ancestor(self, publish_id_a: str, publish_id_b: str) -> Optional[LineageNode]:
        """
        Find the common ancestor of two publishes.
        
        Returns the most recent common ancestor, or None if none exists.
        """
        ancestors_a = {n.publish_id: n for n in self.get_ancestors(publish_id_a)}
        ancestors_b = self.get_ancestors(publish_id_b)
        
        # Find common ancestors
        common = []
        for node in ancestors_b:
            if node.publish_id in ancestors_a:
                common.append((node, ancestors_a[node.publish_id]))
        
        if not common:
            return None
        
        # Return the most recent (highest version) common ancestor
        return max(common, key=lambda x: x[0].version)[0]
    
    def get_provenance(self, publish_id: str) -> Dict[str, Any]:
        """
        Get complete provenance information for a publish.
        
        Returns a dictionary containing:
        - The publish itself
        - All ancestors (what it was derived from)
        - All dependencies
        - Validation history
        """
        publish = self.storage.get_publish(publish_id)
        if not publish:
            raise ValueError(f"Publish not found: {publish_id}")
        
        ancestors = self.get_ancestors(publish_id)
        
        return {
            "publish": publish.model_dump(),
            "ancestors": [n.__dict__ for n in ancestors],
            "ancestor_count": len(ancestors),
            "depth": len(ancestors),
            "lineage_verified": all(
                a.status == EntityStatus.APPROVED for a in ancestors
            ),
        }
    
    def verify_lineage(self, publish_id: str) -> Tuple[bool, List[str]]:
        """
        Verify the integrity of a publish's lineage.
        
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        publish = self.storage.get_publish(publish_id)
        
        if not publish:
            return False, [f"Publish not found: {publish_id}"]
        
        # Verify all parents exist
        for parent_id in publish.dependencies:
            parent = self.storage.get_publish(parent_id)
            if not parent:
                issues.append(f"Parent publish not found: {parent_id}")
            else:
                # Verify parent has this publish as a child
                if publish_id not in parent.child_publish_ids:
                    issues.append(f"Parent {parent_id} does not list {publish_id} as child")
        
        # Verify all children exist
        for child_id in publish.child_publish_ids:
            child = self.storage.get_publish(child_id)
            if not child:
                issues.append(f"Child publish not found: {child_id}")
            else:
                # Verify child has this publish as a parent
                if publish_id not in child.dependencies:
                    issues.append(f"Child {child_id} does not list {publish_id} as parent")
        
        return len(issues) == 0, issues
    
    def find_publishes_by_ancestor(self, ancestor_publish_id: str) -> List[str]:
        """
        Find all publishes that have a specific publish as an ancestor.
        
        Returns a list of publish IDs.
        """
        result = []
        all_publishes = self.storage.list_publishes()
        
        for publish in all_publishes:
            ancestors = self.get_ancestors(publish.publish_id)
            if any(a.publish_id == ancestor_publish_id for a in ancestors):
                result.append(publish.publish_id)
        
        return result
    
    def rollback_to_publish(self, entity_type: str, entity_id: str, target_version: int) -> Optional[Publish]:
        """
        Mark a specific publish version as the current approved version.
        
        This does not delete later publishes, but marks the target as approved
        and later versions as rejected (or pending).
        """
        target = self.storage.get_publish_by_version(entity_type, entity_id, target_version)
        if not target:
            raise ValueError(f"Publish not found: {entity_type}/{entity_id} v{target_version}")
        
        # Mark target as approved
        target.status = EntityStatus.APPROVED
        self.storage.create_publish(target)
        
        # Mark later versions as rejected
        all_publishes = self.storage.list_publishes(entity_type, entity_id)
        for pub in all_publishes:
            if pub.version > target_version and pub.status == EntityStatus.APPROVED:
                pub.status = EntityStatus.REJECTED
                self.storage.create_publish(pub)
        
        return target


# Global lineage tracker instance
_lineage_tracker: Optional[LineageTracker] = None


def get_lineage_tracker(storage: Optional[PipelineStorage] = None) -> LineageTracker:
    """Get the global lineage tracker instance."""
    global _lineage_tracker
    if _lineage_tracker is None:
        _lineage_tracker = LineageTracker(storage)
    return _lineage_tracker

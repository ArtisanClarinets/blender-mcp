"""Tests for pipeline storage."""

import pytest
import tempfile
from pathlib import Path

from blender_mcp.pipeline.storage import PipelineStorage, get_pipeline_storage, reset_storage
from blender_mcp.pipeline.entities import Project, Sequence, Shot, Asset, AssetType, Publish, PublishStage


@pytest.fixture
def temp_storage():
    """Create a temporary storage for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = PipelineStorage(tmpdir)
        yield storage
        reset_storage()


class TestPipelineStorage:
    """Test PipelineStorage class."""
    
    def test_storage_initialization(self, temp_storage):
        """Test storage initialization."""
        assert temp_storage.root.exists()
        assert (temp_storage.root / "projects").exists()
        assert (temp_storage.root / "publishes").exists()
    
    def test_create_and_get_project(self, temp_storage):
        """Test creating and retrieving a project."""
        project = Project(code="TEST", name="Test Project")
        created = temp_storage.create_project(project)
        
        assert created.code == "TEST"
        
        retrieved = temp_storage.get_project("TEST")
        assert retrieved is not None
        assert retrieved.name == "Test Project"
    
    def test_list_projects(self, temp_storage):
        """Test listing projects."""
        # Create multiple projects
        temp_storage.create_project(Project(code="PROJ1", name="Project 1"))
        temp_storage.create_project(Project(code="PROJ2", name="Project 2"))
        
        projects = temp_storage.list_projects()
        assert len(projects) == 2
        codes = {p.code for p in projects}
        assert codes == {"PROJ1", "PROJ2"}
    
    def test_create_and_get_sequence(self, temp_storage):
        """Test creating and retrieving a sequence."""
        # Need a project first
        temp_storage.create_project(Project(code="TEST", name="Test"))
        
        seq = Sequence(code="SEQ01", name="Sequence 1", project_code="TEST")
        created = temp_storage.create_sequence(seq)
        
        assert created.code == "SEQ01"
        
        retrieved = temp_storage.get_sequence("TEST", "SEQ01")
        assert retrieved is not None
        assert retrieved.name == "Sequence 1"
    
    def test_create_and_get_shot(self, temp_storage):
        """Test creating and retrieving a shot."""
        temp_storage.create_project(Project(code="TEST", name="Test"))
        
        shot = Shot(
            name="sh010",
            shot_number=10,
            project_code="TEST",
            sequence_code="SEQ01",
        )
        created = temp_storage.create_shot(shot)
        
        assert created.name == "sh010"
        
        retrieved = temp_storage.get_shot("TEST", "sh010")
        assert retrieved is not None
        assert retrieved.shot_number == 10
    
    def test_create_and_get_asset(self, temp_storage):
        """Test creating and retrieving an asset."""
        temp_storage.create_project(Project(code="TEST", name="Test"))
        
        asset = Asset(
            name="hero",
            asset_type=AssetType.CHARACTER,
            project_code="TEST",
        )
        created = temp_storage.create_asset(asset)
        
        assert created.name == "hero"
        
        retrieved = temp_storage.get_asset("TEST", "character", "hero")
        assert retrieved is not None
        assert retrieved.asset_type == AssetType.CHARACTER
    
    def test_create_and_get_publish(self, temp_storage):
        """Test creating and retrieving a publish."""
        publish = Publish(
            publish_id="shot_sh010_v001_abc123",
            entity_type="shot",
            entity_id="sh010",
            version=1,
            stage=PublishStage.LAYOUT,
        )
        created = temp_storage.create_publish(publish)
        
        assert created.publish_id == "shot_sh010_v001_abc123"
        
        retrieved = temp_storage.get_publish("shot_sh010_v001_abc123")
        assert retrieved is not None
        assert retrieved.version == 1
    
    def test_get_latest_publish(self, temp_storage):
        """Test getting latest publish."""
        # Create publishes in order
        for version in [1, 2, 3]:
            publish = Publish(
                publish_id=f"shot_sh010_v{version:03d}_abc123",
                entity_type="shot",
                entity_id="sh010",
                version=version,
                stage=PublishStage.LAYOUT,
            )
            temp_storage.create_publish(publish)
        
        latest = temp_storage.get_latest_publish("shot", "sh010")
        assert latest is not None
        assert latest.version == 3


class TestGlobalStorage:
    """Test global storage functions."""
    
    def test_get_pipeline_storage_singleton(self):
        """Test that get_pipeline_storage returns singleton."""
        reset_storage()
        storage1 = get_pipeline_storage()
        storage2 = get_pipeline_storage()
        
        assert storage1 is storage2
    
    def test_reset_storage(self):
        """Test reset_storage function."""
        reset_storage()
        storage1 = get_pipeline_storage()
        reset_storage()
        storage2 = get_pipeline_storage()
        
        assert storage1 is not storage2

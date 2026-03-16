"""Tests for pipeline entities."""

import pytest
from datetime import datetime
from blender_mcp.pipeline.entities import (
    Project,
    Sequence,
    Shot,
    Asset,
    AssetType,
    Publish,
    PublishStage,
    EntityStatus,
    generate_publish_id,
    generate_package_id,
)


class TestProject:
    """Test Project entity."""
    
    def test_project_creation(self):
        """Test creating a project."""
        project = Project(
            code="TEST",
            name="Test Project",
            description="A test project",
        )
        
        assert project.code == "TEST"
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.status == EntityStatus.ACTIVE
        assert project.id is not None
    
    def test_project_code_validation(self):
        """Test project code validation."""
        # Valid codes
        Project(code="TEST", name="Test")
        Project(code="test_123", name="Test")
        Project(code="Test-Project", name="Test")
        
        # Invalid codes
        with pytest.raises(ValueError):
            Project(code="", name="Test")  # Empty
        with pytest.raises(ValueError):
            Project(code="123", name="Test")  # Starts with number
        with pytest.raises(ValueError):
            Project(code="test project", name="Test")  # Space


class TestSequence:
    """Test Sequence entity."""
    
    def test_sequence_creation(self):
        """Test creating a sequence."""
        seq = Sequence(
            code="SEQ01",
            name="Sequence 01",
            project_code="TEST",
        )
        
        assert seq.code == "SEQ01"
        assert seq.name == "Sequence 01"
        assert seq.project_code == "TEST"
        assert seq.status == EntityStatus.ACTIVE


class TestShot:
    """Test Shot entity."""
    
    def test_shot_creation(self):
        """Test creating a shot."""
        shot = Shot(
            name="sh010",
            shot_number=10,
            project_code="TEST",
            sequence_code="SEQ01",
            frame_start=1001,
            frame_end=1100,
        )
        
        assert shot.name == "sh010"
        assert shot.shot_number == 10
        assert shot.frame_start == 1001
        assert shot.frame_end == 1100
    
    def test_shot_number_validation(self):
        """Test shot number validation."""
        with pytest.raises(ValueError):
            Shot(
                name="sh000",
                shot_number=0,  # Must be > 0
                project_code="TEST",
                sequence_code="SEQ01",
            )


class TestAsset:
    """Test Asset entity."""
    
    def test_asset_creation(self):
        """Test creating an asset."""
        asset = Asset(
            name="hero_char",
            asset_type=AssetType.CHARACTER,
            project_code="TEST",
        )
        
        assert asset.name == "hero_char"
        assert asset.asset_type == AssetType.CHARACTER
        assert asset.project_code == "TEST"


class TestPublish:
    """Test Publish entity."""
    
    def test_publish_creation(self):
        """Test creating a publish."""
        publish = Publish(
            publish_id="shot:sh010:v001:abc123",
            entity_type="shot",
            entity_id="sh010",
            version=1,
            stage=PublishStage.LAYOUT,
        )
        
        assert publish.publish_id == "shot:sh010:v001:abc123"
        assert publish.entity_type == "shot"
        assert publish.version == 1
        assert publish.stage == PublishStage.LAYOUT


class TestIdGeneration:
    """Test ID generation functions."""
    
    def test_generate_publish_id(self):
        """Test publish ID generation."""
        pid = generate_publish_id("shot", "sh010", 1)
        assert pid.startswith("shot_sh010_v001_")
        assert len(pid) == 24  # base + 8 char hash
        assert ":" not in pid  # Safe for filesystem
    
    def test_generate_package_id(self):
        """Test package ID generation."""
        pid = generate_package_id("asset", "hero", 1)
        assert pid.startswith("usd_asset_hero_v001_")
        assert len(pid) == 28  # base + 8 char hash
        assert ":" not in pid  # Safe for filesystem

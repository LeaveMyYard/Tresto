"""Unit tests for tresto.core.pathfinder module."""

from pathlib import Path

import pytest

from tresto.core.config.main import AIConfig, ProjectConfig, TrestoConfig
from tresto.core.pathfinder import TrestoPathFinder


class TestTrestoPathFinder:
    """Test cases for TrestoPathFinder class."""

    @pytest.fixture
    def sample_config(self) -> TrestoConfig:
        """Create a sample TrestoConfig for testing."""
        return TrestoConfig(
            project=ProjectConfig(name="test_project", url="https://example.com", test_directory="tests"),
            ai=AIConfig(connector="anthropic", model="claude-3-sonnet"),
        )

    def test_init_valid_test_name(self, sample_config: TrestoConfig) -> None:
        """Test initialization with valid test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="auth.login.basic")
        assert pathfinder.config == sample_config
        assert pathfinder.test_name == "auth.login.basic"

    def test_init_simple_test_name(self, sample_config: TrestoConfig) -> None:
        """Test initialization with simple test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="simple_test")
        assert pathfinder.test_name == "simple_test"

    def test_validate_test_name_empty_string(self, sample_config: TrestoConfig) -> None:
        """Test validation fails for empty test name."""
        with pytest.raises(ValueError, match="Test name should contain a module name"):
            TrestoPathFinder(config=sample_config, test_name="")

    def test_validate_test_name_only_separators(self, sample_config: TrestoConfig) -> None:
        """Test validation fails for test name with only separators."""
        with pytest.raises(ValueError, match="Test name should contain a module name"):
            TrestoPathFinder(config=sample_config, test_name="///...")

    def test_validate_test_name_invalid_identifiers(self, sample_config: TrestoConfig) -> None:
        """Test validation fails for invalid Python identifiers."""
        with pytest.raises(ValueError, match="Test name should contain only valid Python identifiers"):
            TrestoPathFinder(config=sample_config, test_name="123invalid.test-name")

    def test_validate_test_name_with_keywords(self, sample_config: TrestoConfig) -> None:
        """Test validation allows Python keywords as they are valid identifiers."""
        # Python keywords are valid identifiers, so this should pass
        pathfinder = TrestoPathFinder(config=sample_config, test_name="class.def.return")
        assert pathfinder.test_name == "class.def.return"

    def test_split_test_path_dots_only(self) -> None:
        """Test splitting path with dots only."""
        result = TrestoPathFinder.split_test_path("module.submodule.test")
        assert result == ["module", "submodule", "test"]

    def test_split_test_path_slashes_only(self) -> None:
        """Test splitting path with slashes only."""
        result = TrestoPathFinder.split_test_path("module/submodule/test")
        assert result == ["module", "submodule", "test"]

    def test_split_test_path_mixed_separators(self) -> None:
        """Test splitting path with mixed dots and slashes."""
        result = TrestoPathFinder.split_test_path("module.submodule/test.name")
        assert result == ["module", "submodule", "test", "name"]

    def test_split_test_path_repeated_separators(self) -> None:
        """Test splitting path with repeated separators."""
        result = TrestoPathFinder.split_test_path("module...submodule///test")
        assert result == ["module", "submodule", "test"]

    def test_split_test_path_empty_string(self) -> None:
        """Test splitting empty string."""
        result = TrestoPathFinder.split_test_path("")
        assert result == []

    def test_split_test_path_single_part(self) -> None:
        """Test splitting single part."""
        result = TrestoPathFinder.split_test_path("test")
        assert result == ["test"]

    def test_tresto_root_property(self, sample_config: TrestoConfig) -> None:
        """Test tresto_root property returns correct path."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="test")
        assert pathfinder.tresto_root == Path("tests")

    def test_test_module_relative_path_simple(self, sample_config: TrestoConfig) -> None:
        """Test test_module_relative_path for simple test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="simple")
        assert pathfinder.test_module_relative_path == Path("test_simple.py")

    def test_test_module_relative_path_nested(self, sample_config: TrestoConfig) -> None:
        """Test test_module_relative_path for nested test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="auth.login.basic")
        assert pathfinder.test_module_relative_path == Path("auth/login/test_basic.py")

    def test_test_module_relative_path_deep_nested(self, sample_config: TrestoConfig) -> None:
        """Test test_module_relative_path for deeply nested test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="a.b.c.d.e.test")
        assert pathfinder.test_module_relative_path == Path("a/b/c/d/e/test_test.py")

    def test_test_file_path_simple(self, sample_config: TrestoConfig) -> None:
        """Test test_file_path for simple test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="simple")
        expected = Path("tests/test_simple.py")
        assert pathfinder.test_file_path == expected

    def test_test_file_path_nested(self, sample_config: TrestoConfig) -> None:
        """Test test_file_path for nested test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="auth.login.basic")
        expected = Path("tests/auth/login/test_basic.py")
        assert pathfinder.test_file_path == expected

    def test_recording_module_relative_path_simple(self, sample_config: TrestoConfig) -> None:
        """Test recording_module_relative_path for simple test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="simple")
        assert pathfinder.recording_module_relative_path == Path("recording_simple.py")

    def test_recording_module_relative_path_nested(self, sample_config: TrestoConfig) -> None:
        """Test recording_module_relative_path for nested test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="auth.login.basic")
        assert pathfinder.recording_module_relative_path == Path("auth/login/recording_basic.py")

    def test_recording_file_path_simple(self, sample_config: TrestoConfig) -> None:
        """Test recording_file_path for simple test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="simple")
        expected = Path("tests/.recordings/recording_simple.py")
        assert pathfinder.recording_file_path == expected

    def test_recording_file_path_nested(self, sample_config: TrestoConfig) -> None:
        """Test recording_file_path for nested test name."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="auth.login.basic")
        expected = Path("tests/.recordings/auth/login/recording_basic.py")
        assert pathfinder.recording_file_path == expected

    def test_different_test_directory(self) -> None:
        """Test pathfinder with different test directory."""
        config = TrestoConfig(
            project=ProjectConfig(name="test_project", url="https://example.com", test_directory="my_tests"),
            ai=AIConfig(connector="anthropic", model="claude-3-sonnet"),
        )

        pathfinder = TrestoPathFinder(config=config, test_name="feature.test")
        assert pathfinder.tresto_root == Path("my_tests")
        assert pathfinder.test_file_path == Path("my_tests/feature/test_test.py")
        assert pathfinder.recording_file_path == Path("my_tests/.recordings/feature/recording_test.py")

    def test_complex_path_scenarios(self, sample_config: TrestoConfig) -> None:
        """Test various complex path scenarios."""
        test_cases = [
            ("a", Path("test_a.py"), Path("recording_a.py")),
            ("a.b", Path("a/test_b.py"), Path("a/recording_b.py")),
            ("a/b/c", Path("a/b/test_c.py"), Path("a/b/recording_c.py")),
            ("a.b.c.d.e", Path("a/b/c/d/test_e.py"), Path("a/b/c/d/recording_e.py")),
            ("module/sub.test", Path("module/sub/test_test.py"), Path("module/sub/recording_test.py")),
        ]

        for test_name, expected_test_path, expected_recording_path in test_cases:
            pathfinder = TrestoPathFinder(config=sample_config, test_name=test_name)
            assert pathfinder.test_module_relative_path == expected_test_path
            assert pathfinder.recording_module_relative_path == expected_recording_path

    def test_edge_case_underscores_in_names(self, sample_config: TrestoConfig) -> None:
        """Test handling of underscores in test names."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="auth_module.user_login.test_basic")
        assert pathfinder.test_module_relative_path == Path("auth_module/user_login/test_test_basic.py")
        assert pathfinder.recording_module_relative_path == Path("auth_module/user_login/recording_test_basic.py")

    def test_edge_case_numbers_in_names(self, sample_config: TrestoConfig) -> None:
        """Test handling of numbers in test names."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="test2.module3.case1")
        assert pathfinder.test_module_relative_path == Path("test2/module3/test_case1.py")
        assert pathfinder.recording_module_relative_path == Path("test2/module3/recording_case1.py")

    def test_property_consistency(self, sample_config: TrestoConfig) -> None:
        """Test that all properties return consistent paths."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="auth.login.basic")

        # Test that absolute paths are built correctly from relative paths
        assert pathfinder.test_file_path == pathfinder.tresto_root / pathfinder.test_module_relative_path
        assert (
            pathfinder.recording_file_path
            == pathfinder.tresto_root / ".recordings" / pathfinder.recording_module_relative_path
        )

    def test_pathfinder_immutability(self, sample_config: TrestoConfig) -> None:
        """Test that pathfinder properties are consistent across multiple calls."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="auth.login.basic")

        # Call properties multiple times and ensure they return the same values
        for _ in range(3):
            assert pathfinder.tresto_root == Path("tests")
            assert pathfinder.test_module_relative_path == Path("auth/login/test_basic.py")
            assert pathfinder.test_file_path == Path("tests/auth/login/test_basic.py")
            assert pathfinder.recording_module_relative_path == Path("auth/login/recording_basic.py")
            assert pathfinder.recording_file_path == Path("tests/.recordings/auth/login/recording_basic.py")

    def test_pydantic_model_behavior(self, sample_config: TrestoConfig) -> None:
        """Test that TrestoPathFinder behaves correctly as a Pydantic model."""
        pathfinder = TrestoPathFinder(config=sample_config, test_name="test.name")

        # Test model dump
        model_dict = pathfinder.model_dump()
        assert "config" in model_dict
        assert "test_name" in model_dict
        assert model_dict["test_name"] == "test.name"

        # Test model copy
        pathfinder_copy = pathfinder.model_copy()
        assert pathfinder_copy.test_name == pathfinder.test_name
        assert pathfinder_copy.config == pathfinder.config

        # Test model copy with updates
        updated_pathfinder = pathfinder.model_copy(update={"test_name": "new.test"})
        assert updated_pathfinder.test_name == "new.test"
        assert updated_pathfinder.config == pathfinder.config

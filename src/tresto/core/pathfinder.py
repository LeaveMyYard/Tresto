from pathlib import Path

from pydantic import BaseModel, field_validator

from tresto.core.config.main import TrestoConfig


class TrestoPathFinder(BaseModel):
    config: TrestoConfig
    test_name: str

    @field_validator("test_name")
    def validate_test_name(cls, v: str) -> str:
        """
        Test name should contain a path in the following format:
        <module_name>/<submodule_name>/<test_name>
        or
        <module_name>.<submodule_name>.<test_name>
        """

        parts = cls.split_test_path(v)
        if len(parts) == 0:
            raise ValueError("Test name should contain a module name")

        # TODO: Is this a correct check?
        if any(not n.isidentifier() for n in parts):
            raise ValueError("Test name should contain only valid Python identifiers")

        return v

    @staticmethod
    def split_test_path(raw_path: str) -> list[str]:
        # allow dots or slashes as separators; collapse repeated separators
        return [p for chunk in raw_path.split("/") for p in chunk.split(".") if p]

    @property
    def tresto_root(self) -> Path:
        return Path(self.config.project.test_directory)

    @property
    def test_module_relative_path(self) -> Path:
        parts = self.split_test_path(self.test_name)
        test_file_name = f"test_{parts[-1]}.py"
        return Path(*parts[:-1]) / test_file_name

    @property
    def test_file_path(self) -> Path:
        return self.tresto_root / self.test_module_relative_path

    @property
    def recording_module_relative_path(self) -> Path:
        parts = self.split_test_path(self.test_name)
        test_file_name = f"recording_{parts[-1]}.py"
        return Path(*parts[:-1]) / test_file_name

    @property
    def recording_file_path(self) -> Path:
        return self.tresto_root / ".recordings" / self.recording_module_relative_path

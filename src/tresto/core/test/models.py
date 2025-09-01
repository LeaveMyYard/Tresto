from dataclasses import dataclass

from tresto.ai.agent.tools.inspect.recording import RecordingManager


@dataclass
class TestRunResult:
    success: bool
    duration_s: float
    traceback: str | None = None
    stdout: str | None = None
    stderr: str | None = None

    # Recording manager with time-based access to artifacts
    recording: RecordingManager | None = None

    def __str__(self) -> str:
        return (
            f"Success: {self.success}\n"
            + f"Duration: {self.duration_s:.2f} seconds\n"
            + (f"Stdout: \n```\n{self.stdout}\n```\n" if self.stdout else "")
            + (f"Stderr: \n```\n{self.stderr}\n```\n" if self.stderr else "")
            + (f"Traceback: \n```\n{self.traceback}\n```\n" if self.traceback else "")
        )

"""Browser recording launcher for Tresto using Playwright codegen."""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class BrowserRecorder:
    """Thin wrapper around the Playwright code generator CLI.

    This class launches `playwright codegen --target python-async -o <file> [url]` and
    waits for the user to finish recording. When the recorder window is closed,
    the generated script (if any) will be available at the requested path.
    """

    def __init__(self, config: Any | None = None, headless: bool = False) -> None:
        self.config = config
        self.headless = headless  # Unused by codegen; retained for API compatibility

    async def start_recording(
        self,
        url: str = "",
        output_file: str | Path | None = None,
        extra_args: list[str] | None = None,
    ) -> str:
        """Start Playwright codegen and wait until the user stops recording.

        Parameters
        - url: Optional URL to open when codegen starts
        - output_file: Destination path for the generated script
        - extra_args: Additional CLI flags to pass to `playwright codegen`

        Returns the generated code.
        """

        # Resolve output path
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join("tresto_recordings", f"codegen_{timestamp}.py")

        if isinstance(output_file, str):
            output_file = Path(output_file)

        output_abs_path = os.path.abspath(output_file)
        os.makedirs(os.path.dirname(output_abs_path), exist_ok=True)

        # Build command args
        cli_args: list[str] = ["codegen", "--target", "python-async", "-o", output_abs_path]
        if extra_args:
            cli_args.extend(extra_args)
        if url:
            cli_args.append(url)

        # Try the `playwright` executable; fall back to `python -m playwright`
        command_variants: list[list[str]] = [
            ["playwright", *cli_args],
            [sys.executable, "-m", "playwright", *cli_args],
        ]

        last_error: Exception | None = None
        return_code: int | None = None

        for command in command_variants:
            try:
                process = await asyncio.create_subprocess_exec(*command)
                return_code = await process.wait()
                break
            except FileNotFoundError as exc:
                last_error = exc
                continue

        succeeded = return_code == 0 and os.path.exists(output_abs_path)

        if not succeeded:
            raise RuntimeError(f"Failed to record browser interaction: {last_error}")

        return Path(output_abs_path).read_text()

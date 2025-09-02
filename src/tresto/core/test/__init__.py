from __future__ import annotations

import time
from traceback import format_exc
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from PIL.Image import Image

from .models import TestRunResult
from .run import run_test

if TYPE_CHECKING:
    from pathlib import Path

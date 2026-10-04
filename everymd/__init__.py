"""everymd: every document -> Markdown that AI can use."""

__version__ = "0.1.0"

from .api import ConvertResult, convert  # noqa: E402
from .detect import UnsupportedInput, detect  # noqa: E402

__all__ = ["ConvertResult", "UnsupportedInput", "__version__", "convert", "detect"]

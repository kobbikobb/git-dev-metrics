from datetime import datetime
from pathlib import Path


def get_default_output_path(period: str = "") -> Path:
    """Default output path with timestamp; appends period slug when provided."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    slug = period.replace("_", "-")
    suffix = f"_{slug}" if slug else ""
    return Path(f"./metrics_results/metrics_{timestamp}{suffix}.md")

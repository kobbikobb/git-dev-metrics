from datetime import datetime
from pathlib import Path


def get_default_output_path() -> Path:
    """Get default output path with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return Path(f"./metrics_results/metrics_{timestamp}.md")

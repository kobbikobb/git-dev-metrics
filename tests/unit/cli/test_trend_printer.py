import json
import re

from git_dev_metrics.metrics.printer.trend import FileTrendPrinter
from git_dev_metrics.metrics.trend_calculator import TrendDataset


def _data_block(html: str) -> dict:
    match = re.search(r"const DATA = (\{.*?\});", html, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


class TestFileTrendPrinter:
    def test_should_render_canvases_and_embed_dataset(self, tmp_path):
        # Arrange
        dataset = TrendDataset(
            months=["2026-02"],
            devs=[
                {
                    "label": "Same label",
                    "data": [
                        {
                            "month_label": "Feb 2026",
                            "month_key": "2026-02",
                            "pr_count": count,
                            "cycle_hours": 12.5,
                            "ai_pct": 50.0,
                        }
                    ],
                }
                for count in (1, 2)
            ],
        )
        output = tmp_path / "t.html"

        # Act
        FileTrendPrinter(output).render(dataset)

        # Assert
        content = output.read_text()
        assert 'id="prs"' in content
        assert 'id="cycle"' in content
        assert 'id="ai"' in content
        data = _data_block(content)
        assert [dev["label"] for dev in data["devs"]] == ["Same label", "Same label"]
        assert [dev["data"][0]["pr_count"] for dev in data["devs"]] == [1, 2]
        assert data["months"] == ["2026-02"]

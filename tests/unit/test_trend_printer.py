import json
import re

from git_dev_metrics.metrics.printer.trend import FileTrendPrinter
from git_dev_metrics.metrics.trend_calculator import DevMonthRow, TrendDataset


def _data_block(html: str) -> dict:
    match = re.search(r"const DATA = (\{.*?\});", html, re.DOTALL)
    assert match is not None
    return json.loads(match.group(1))


class TestFileTrendPrinter:
    def test_should_render_canvases_and_embed_dataset(self, tmp_path):
        # Arrange
        dataset = TrendDataset(
            months=["2026-02", "2026-03"],
            devs=["alice", "bob"],
            rows={
                "alice": [
                    DevMonthRow("Feb 2026", "2026-02", 2, 12.5, 50.0),
                    DevMonthRow("Mar 2026", "2026-03", 3, 10.0, 60.0),
                ],
                "bob": [
                    DevMonthRow("Feb 2026", "2026-02", 1, 8.0, 0.0),
                    DevMonthRow("Mar 2026", "2026-03", 2, 9.0, 100.0),
                ],
            },
        )
        output = tmp_path / "t.html"

        # Act
        FileTrendPrinter(output).render(dataset, "myorg", "myrepo")

        # Assert
        content = output.read_text()
        assert 'id="prs"' in content
        assert 'id="cycle"' in content
        assert 'id="ai"' in content
        data = _data_block(content)
        assert data["devs"] == ["alice", "bob"]
        assert data["months"] == ["2026-02", "2026-03"]

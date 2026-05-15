"""CLI surface after legacy analyze command and anon module removal."""

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from git_dev_metrics.cli.app import app

REPO_ROOT = Path(__file__).resolve().parents[3]


class TestNoSubcommand:
    def test_should_show_help_listing_active_subcommands(self):
        runner = CliRunner()

        result = runner.invoke(app, [])

        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "pull" in result.output
        assert "summary" in result.output
        assert "dashboard" in result.output
        assert "trend" in result.output
        assert "stale" in result.output
        assert "clear" in result.output
        assert "logout" in result.output
        assert "analyze" not in result.output
        assert "report" not in result.output
        forbidden = "anon" + "ymize"
        assert forbidden not in result.output


class TestAnalyzeRemoved:
    def test_should_reject_analyze_subcommand(self):
        runner = CliRunner()

        result = runner.invoke(app, ["analyze", "--org", "x"])

        assert result.exit_code != 0
        combined = (result.output or "") + (result.stderr or "")
        assert any(marker in combined for marker in ("No such command", "Error", "Usage:"))


class TestAnonymizeFullyRemoved:
    def test_should_have_no_anon_references_in_sources_or_tests(self):
        pattern = "anon" + "ymize"

        result = subprocess.run(
            [
                "grep",
                "-rn",
                "--exclude-dir=.claude",
                "--exclude-dir=__pycache__",
                pattern,
                "git_dev_metrics/",
                "tests/",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
        )

        assert result.returncode == 1
        assert result.stdout == b""

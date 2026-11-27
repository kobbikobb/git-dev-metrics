from dataclasses import replace
from pathlib import Path

from ..cache import get_hidden_logins, get_nicknames, load_all_repos_by_month
from ..models import PullRequest
from ..utils import TimePeriod
from ._stale_pr import StalePr
from .lang_calculator import LangDataset, build_lang_dataset
from .skill_calculator import SkillDataset, build_skill_dataset
from .snapshot import MetricsSnapshot
from .team_velocity_calculator import TeamVelocityDataset, build_team_velocity_dataset
from .trend_calculator import TrendDataset, build_trend_dataset


class ReportData:
    """Prepare named report results using the selected database's display preferences."""

    def __init__(self, db_path: Path | None) -> None:
        self._db_path = db_path
        self._hidden = get_hidden_logins(db_path)
        self._names = {login.lower(): name for login, name in get_nicknames(db_path).items()}

    def _display_name(self, login: str) -> str | None:
        key = login.lower()
        return None if key in self._hidden else self._names.get(key, login)

    def stale(self, prs: list[StalePr]) -> list[StalePr]:
        return [
            replace(pr, author=self._display_name(pr.author)) if pr.author else pr for pr in prs
        ]

    def snapshot(
        self,
        repo_prs: dict[str, list[PullRequest]],
        period: TimePeriod,
        *,
        has_partial: bool = False,
    ) -> MetricsSnapshot:
        return MetricsSnapshot.from_repo_prs(
            repo_prs, period, has_partial=has_partial, display_name=self._display_name
        )

    def languages(self, prs: list[dict]) -> LangDataset:
        return build_lang_dataset(prs, self._display_name)

    def skills(self, prs: list[dict]) -> SkillDataset:
        return build_skill_dataset(prs, self._display_name)

    def trend(self, months: list[tuple[int, int]]) -> TrendDataset | None:
        prs = load_all_repos_by_month(months, db_path=self._db_path)
        return build_trend_dataset(months, prs, self._display_name) if any(prs.values()) else None

    def velocity(self, months: list[tuple[int, int]]) -> TeamVelocityDataset | None:
        prs = load_all_repos_by_month(months, db_path=self._db_path)
        return (
            build_team_velocity_dataset(months, prs, self._display_name)
            if any(prs.values())
            else None
        )

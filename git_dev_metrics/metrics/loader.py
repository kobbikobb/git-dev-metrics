from pathlib import Path

from ..cache import has_partial_for_range, load_all_repos_for_range
from ..utils.date_utils import month_iter, parse_year_month, range_period
from .snapshot import MetricsSnapshot


class InvalidRangeError(ValueError):
    pass


def load_snapshot_for_months(
    months: list[tuple[int, int]], db_path: Path | None
) -> MetricsSnapshot | None:
    repo_prs = load_all_repos_for_range(months, db_path=db_path)
    if not repo_prs:
        return None
    period = range_period(months[0], months[-1])
    partial = has_partial_for_range(months, db_path=db_path)
    return MetricsSnapshot.from_repo_prs(repo_prs, period, has_partial=partial)


def load_snapshot_for_range(from_: str, to: str, db_path: Path | None) -> MetricsSnapshot | None:
    from_ym = parse_year_month(from_)
    to_ym = parse_year_month(to)
    if to_ym < from_ym:
        raise InvalidRangeError("--to must be >= --from.")
    months = month_iter(from_ym, to_ym)
    return load_snapshot_for_months(months, db_path)

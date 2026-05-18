from ..models import PullRequest
from ._raw_metrics import RawMetrics, compute_raw
from .calculator import calculate_reviews_given, group_prs_by_devs


def compute_dev_metrics(
    all_prs: list[PullRequest], days: int, reviewer_counts: dict[str, int]
) -> dict[str, RawMetrics]:
    return {
        dev: compute_raw(dev_prs, days, reviewer_counts.get(dev, 0))
        for dev, dev_prs in group_prs_by_devs(all_prs).items()
    }


def compute_repo_metrics(
    repo_prs: dict[str, list[PullRequest]], days: int
) -> dict[str, RawMetrics]:
    raws: dict[str, RawMetrics] = {}
    for name, prs in repo_prs.items():
        reviews_given = sum(calculate_reviews_given(prs).values())
        raw = compute_raw(prs, days, reviews_given)
        if raw.pr_count > 0:
            raws[name] = raw
    return raws

from pathlib import Path

from .._stale_pr import StalePr, summarize_stale_prs
from ._html_templates import render_template


def _target_status(
    targets: dict[str, float], total: int, avg_age: float, stale_prs: list[StalePr]
) -> dict:
    items: list[dict] = []
    met = 0

    if "stale_max_count" in targets:
        t = targets["stale_max_count"]
        ok = total <= t
        if ok:
            met += 1
        items.append(dict(label="Count", actual=total, target=t, ok=ok, unit=""))

    if "stale_max_avg_age_days" in targets:
        t = targets["stale_max_avg_age_days"]
        ok = avg_age <= t
        if ok:
            met += 1
        items.append(dict(label="Avg age", actual=round(avg_age, 1), target=t, ok=ok, unit="d"))

    max_age = max((pr.age_days for pr in stale_prs), default=0.0)
    if "stale_max_pr_age_days" in targets:
        t = targets["stale_max_pr_age_days"]
        ok = max_age <= t
        if ok:
            met += 1
        items.append(dict(label="Max age", actual=round(max_age, 1), target=t, ok=ok, unit="d"))

    return {"items": items, "met": met, "total": len(items)}


class FileStaleHtmlPrinter:
    def __init__(self, output_path: Path) -> None:
        self._output_path = output_path

    def render(self, stale_prs: list[StalePr], targets: dict[str, float] | None = None) -> None:
        total, avg_age = summarize_stale_prs(stale_prs)
        ctx = {"total": total, "avg_age": avg_age, "prs": stale_prs, "targets": None}
        if targets:
            ctx["targets"] = _target_status(targets, total, avg_age, stale_prs)
        html = render_template("stale.html", **ctx)
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        self._output_path.write_text(html)

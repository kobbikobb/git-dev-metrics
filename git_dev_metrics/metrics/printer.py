from rich.console import Console
from rich.table import Table


def print_metrics(metrics, org, repo, period):
    console = Console()

    overall_table = Table(title=f"Repo Metrics (last {period})")
    for col in [
        "Repo",
        "Pickup Time (h)",
        "Review Time (h)",
        "Cycle Time (h)",
        "PR Size",
        "Total PRs",
        "PRs/Week",
        "Reviews Given",
    ]:
        overall_table.add_column(col)

    overall_table.add_row(
        f"{org}/{repo}",
        f"{metrics['pickup_time']:.2f}",
        f"{metrics['review_time']:.2f}",
        f"{metrics['cycle_time']:.2f}",
        f"{metrics['pr_size']:.1f}",
        f"{metrics['pr_count']:.0f}",
        f"{metrics['prs_per_week']:.2f}",
        f"{metrics['reviews_given']:.0f}",
    )

    console.print("\n")
    console.print(overall_table)

    dev_table = Table(title="Developer Metrics")
    for col in [
        "Dev",
        "Pickup Time (h)",
        "Review Time (h)",
        "Cycle Time (h)",
        "PR Size",
        "Total PRs",
        "PRs/Week",
        "Reviews Given",
    ]:
        dev_table.add_column(col)

    for dev, m in sorted(
        metrics["dev_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
    ):
        dev_table.add_row(
            dev,
            f"{m['pickup_time']:.2f}",
            f"{m['review_time']:.2f}",
            f"{m['cycle_time']:.2f}",
            f"{m['pr_size']:.1f}",
            f"{m['pr_count']:.0f}",
            f"{m['prs_per_week']:.2f}",
            f"{m['reviews_given']:.0f}",
        )

    console.print(dev_table)


def print_combined_metrics(metrics, period):
    console = Console()

    repo_table = Table(title=f"Repo Metrics (last {period})")
    for col in [
        "Repo",
        "Pickup Time (h)",
        "Review Time (h)",
        "Cycle Time (h)",
        "PR Size",
        "Total PRs",
        "PRs/Week",
        "Reviews Given",
    ]:
        repo_table.add_column(col)

    for repo_name, m in sorted(
        metrics["repo_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
    ):
        repo_table.add_row(
            repo_name,
            f"{m['pickup_time']:.2f}",
            f"{m['review_time']:.2f}",
            f"{m['cycle_time']:.2f}",
            f"{m['pr_size']:.1f}",
            f"{m['pr_count']:.0f}",
            f"{m['prs_per_week']:.2f}",
            f"{m['reviews_given']:.0f}",
        )

    console.print("\n")
    console.print(repo_table)

    dev_table = Table(title="Developer Metrics (combined)")
    for col in [
        "Dev",
        "Pickup Time (h)",
        "Review Time (h)",
        "Cycle Time (h)",
        "PR Size",
        "Total PRs",
        "PRs/Week",
        "Reviews Given",
    ]:
        dev_table.add_column(col)

    for dev, m in sorted(
        metrics["dev_metrics"].items(), key=lambda x: x[1]["pr_count"], reverse=True
    ):
        dev_table.add_row(
            dev,
            f"{m['pickup_time']:.2f}",
            f"{m['review_time']:.2f}",
            f"{m['cycle_time']:.2f}",
            f"{m['pr_size']:.1f}",
            f"{m['pr_count']:.0f}",
            f"{m['prs_per_week']:.2f}",
            f"{m['reviews_given']:.0f}",
        )

    console.print(dev_table)

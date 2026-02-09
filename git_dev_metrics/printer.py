from rich.console import Console
from rich.table import Table


def print_metrics(metrics, org, repo, period):
    console = Console()

    overall_table = Table(title=f"Repo Metrics (last {period})")
    for col in ["Repo", "Cycle Time (h)", "PR Size", "Throughput"]:
        overall_table.add_column(col)

    overall_table.add_row(
        f"{org}/{repo}",
        f"{metrics['cycle_time']:.2f}",
        f"{metrics['pr_size']:.1f}",
        f"{metrics['throughput']:.2f}",
    )

    console.print("\n")
    console.print(overall_table)

    dev_table = Table(title="Developer Metrics")
    for col in ["Dev", "Cycle Time (h)", "PR Size", "Throughput"]:
        dev_table.add_column(col)

    for dev, m in sorted(
        metrics["dev_metrics"].items(), key=lambda x: x[1]["throughput"], reverse=True
    ):
        dev_table.add_row(
            dev,
            f"{m['cycle_time']:.2f}",
            f"{m['pr_size']:.1f}",
            f"{m['throughput']:.2f}",
        )

    console.print(dev_table)

from ..health import calculate_dev_health_score, format_health, get_health_color

DEV_COLUMNS = [
    "Dev",
    "Health",
    "Pickup Time (h)",
    "Review Time (h)",
    "Cycle Time (h)",
    "PR Size",
    "Avg Lines/PR",
    "Total PRs",
    "PRs/Week",
    "Reviews Given",
    "AI",
]


class ConsoleDevPrinter:
    """Print dev metrics to console using Rich."""

    def print_combined_metrics(
        self, metrics: dict, period: str, date_range: str | None = None
    ) -> None:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        title = (
            f"Developer Metrics ({date_range})" if date_range else ("Developer Metrics (combined)")
        )
        table = Table(title=title)
        for col in DEV_COLUMNS:
            table.add_column(col)

        all_dev_metrics = list(metrics["dev_metrics"].values())

        sorted_devs = []
        for dev, m in metrics["dev_metrics"].items():
            health = calculate_dev_health_score(m, all_dev_metrics)
            sorted_devs.append((dev, m, health))

        sorted_devs.sort(key=lambda x: x[2], reverse=True)

        for dev, m, health in sorted_devs:
            color = get_health_color(health)
            table.add_row(
                dev,
                f"[{color}]{format_health(health)}[/{color}]",
                f"{m['pickup_time']:.2f}",
                f"{m['review_time']:.2f}",
                f"{m['cycle_time']:.2f}",
                f"{m['pr_size']:.1f}",
                f"{m.get('avg_lines_per_pr', 0):.1f}",
                f"{m['pr_count']:.0f}",
                f"{m['prs_per_week']:.2f}",
                f"{m['reviews_given']:.0f}",
                f"{m['ai_percentage']:.0f}%",
            )

        console.print(table)

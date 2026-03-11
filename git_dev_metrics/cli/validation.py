import typer

def validate_period(period: str) -> str:
    if not period.endswith("d") or not period[:-1].isdigit():
        raise typer.BadParameter("Period must be like '7d', '30d', '90d'") from None
    return period

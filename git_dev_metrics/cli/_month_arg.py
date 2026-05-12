import typer

from ..utils.date_utils import parse_year_month


def parse_month_arg(value: str, flag: str = "--month") -> tuple[int, int]:
    """Parse a YYYY-MM CLI argument, exiting with a typer-styled error on bad input."""
    try:
        return parse_year_month(value)
    except ValueError as e:
        typer.secho(f"Invalid {flag} '{value}'; expected YYYY-MM.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from e

import typer

from .clear import clear
from .logout import logout
from .pull import pull
from .report import report
from .trend import trend

app = typer.Typer(help="Git development metrics CLI.")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Git development metrics CLI."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


app.command()(clear)
app.command()(logout)
app.command()(pull)
app.command()(report)
app.command()(trend)

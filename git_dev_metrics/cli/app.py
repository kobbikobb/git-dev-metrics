import typer

from .analyze import analyze
from .logout import logout

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Git development metrics CLI."""
    if ctx.invoked_subcommand is None:
        analyze(org=None, repo=None, period=None, output=None, verbose=False, log_level="WARNING")


app.command()(analyze)
app.command()(logout)

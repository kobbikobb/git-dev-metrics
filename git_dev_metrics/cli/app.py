import typer

from .analyze import analyze
from .logout import logout

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Git development metrics CLI."""
    if ctx.invoked_subcommand is None:
        analyze(output=None, verbose=False)


app.command()(analyze)
app.command()(logout)

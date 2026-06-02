import typer

from .clear import clear
from .dashboard import dashboard
from .lang_report import lang_report
from .logout import logout
from .nickname import nickname
from .pull import pull
from .skill_report import skill_report
from .stale import stale
from .summary import summary
from .trend import trend

app = typer.Typer(help="Git development metrics CLI.")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Git development metrics CLI."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


app.command()(clear)
app.command()(dashboard)
app.command()(skill_report)
app.command()(lang_report)
app.command()(logout)
app.command()(nickname)
app.command()(pull)
app.command()(stale)
app.command()(summary)
app.command()(trend)

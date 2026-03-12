import typer

from .analyze import analyze

app = typer.Typer()
app.command()(analyze)

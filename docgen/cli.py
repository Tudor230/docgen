import typer
from docgen.core.loader import load_backend
from docgen.core.generator import generate_markdown
from docgen.core.writer import write_docs
from pathlib import Path
from rich import print

app = typer.Typer(help="Generate API documentation from backend source code.")

@app.command()
def generate(
    backend: str = typer.Option(..., help="Backend name (e.g. flask, express)"),
    input: str = typer.Option(..., help="Path to source code"),
    output: str = typer.Option(..., help="Directory to output docs")
):
    """Generate API docs."""
    print(f"[bold cyan]Generating docs for [green]{backend}[/green] backend...[/bold cyan]")
    parser = load_backend(backend)
    routes = parser.parse_api(Path(input))
    markdown = generate_markdown(routes)
    write_docs(Path(output), markdown)
    print(f"[bold green]Docs written to {output}/API_DOCS.md ✅[/bold green]")

if __name__ == "__main__":
    app()
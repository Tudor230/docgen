import typer
from docgen.core.loader import load_backend
from docgen.core.generator import generate_docs
from docgen.core.writer import write_docs
from pathlib import Path
from rich import print
from typing import Optional

app = typer.Typer(help="Generate API documentation from backend source code.")

@app.command()
def generate(
    backend: str = typer.Option(..., help="Backend name (e.g. flask, express)"),
    input: str = typer.Option(..., help="Path to source code"),
    output: str = typer.Option(..., help="Directory to output docs"),
    format: str = typer.Option("markdown", help="Output format: 'markdown', 'html', or 'both'")
):
    """Generate API docs in markdown, HTML, or both formats."""
    print(f"[bold cyan]Generating docs for [green]{backend}[/green] backend...[/bold cyan]")
    
    # Load backend parser and extract routes
    parser = load_backend(backend)
    routes = parser.parse_api(Path(input))
    
    output_path = Path(output)
    
    if format.lower() == "both":
        # Generate both formats
        print("[cyan]Generating markdown documentation...[/cyan]")
        markdown_content = generate_docs(routes, "markdown")
        write_docs(output_path, markdown_content, "markdown")
        print(f"[green]✅ Markdown docs written to {output_path}/API_DOCS.md[/green]")
        
        print("[cyan]Generating HTML website...[/cyan]")
        html_content = generate_docs(routes, "html")
        write_docs(output_path, html_content, "html")
        print(f"[green]✅ HTML website written to {output_path}/index.html[/green]")
        
        print(f"[bold green]All documentation generated successfully! 🎉[/bold green]")
    else:
        # Generate single format
        format_name = format.lower()
        if format_name not in ['markdown', 'html']:
            print(f"[red]Error: Unsupported format '{format}'. Use 'markdown', 'html', or 'both'[/red]")
            raise typer.Exit(1)
        
        print(f"[cyan]Generating {format_name} documentation...[/cyan]")
        content = generate_docs(routes, format_name)
        write_docs(output_path, content, format_name)
        
        if format_name == "html":
            print(f"[bold green]HTML website written to {output_path}/index.html ✅[/bold green]")
        else:
            print(f"[bold green]Docs written to {output_path}/API_DOCS.md ✅[/bold green]")

if __name__ == "__main__":
    app()
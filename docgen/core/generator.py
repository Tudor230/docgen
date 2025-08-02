from jinja2 import Environment, FileSystemLoader
from pathlib import Path

def generate_markdown(routes):
    """Generate markdown documentation from routes."""
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / "templates")))
    template = env.get_template("markdown.j2")
    return template.render(routes=routes)

def generate_html(routes):
    """Generate HTML documentation from routes."""
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / "templates")))
    template = env.get_template("base.html")
    return template.render(routes=routes)

def generate_docs(routes, format_type="markdown"):
    """Generate documentation in the specified format."""
    if format_type.lower() == "html":
        return generate_html(routes)
    elif format_type.lower() == "markdown":
        return generate_markdown(routes)
    else:
        raise ValueError(f"Unsupported format: {format_type}. Supported formats: 'markdown', 'html'")
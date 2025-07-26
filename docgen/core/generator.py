from jinja2 import Environment, FileSystemLoader
from pathlib import Path

def generate_markdown(routes):
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / "templates")))
    template = env.get_template("markdown.j2")
    return template.render(routes=routes)
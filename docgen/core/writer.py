from pathlib import Path
import shutil

def write_docs(output_path, content, format_type="markdown"):
    """Write documentation to the specified output path."""
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if format_type.lower() == "markdown":
        write_markdown_docs(output_dir, content)
    elif format_type.lower() == "html":
        write_html_docs(output_dir, content)
    else:
        raise ValueError(f"Unsupported format: {format_type}")

def write_markdown_docs(output_path, content):
    """Write markdown documentation."""
    file_path = output_path / "API_DOCS.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def write_html_docs(output_path, content):
    """Write HTML documentation with static assets."""
    # Write the main HTML file
    html_file = output_path / "index.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Copy static assets (CSS and JS)
    templates_dir = Path(__file__).parent.parent / "templates"
    
    # Copy CSS
    css_src = templates_dir / "styles.css"
    css_dst = output_path / "styles.css"
    if css_src.exists():
        shutil.copy2(css_src, css_dst)
    
    # Copy JS
    js_src = templates_dir / "script.js"
    js_dst = output_path / "script.js"
    if js_src.exists():
        shutil.copy2(js_src, js_dst)
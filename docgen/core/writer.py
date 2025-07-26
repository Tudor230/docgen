from pathlib import Path

def write_docs(output_path, content):
    Path(output_path).mkdir(parents=True, exist_ok=True)
    file_path = Path(output_path) / "API_DOCS.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
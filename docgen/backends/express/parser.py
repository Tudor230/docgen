import subprocess
import json
from pathlib import Path

def parse_api(input_path):
    js_script = Path(__file__).parent / "parser.js"
    result = subprocess.run(
        ["node", str(js_script), str(input_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Express parser failed: {result.stderr}")

    return json.loads(result.stdout)
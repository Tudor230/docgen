from docgen.backends.flask import parser
import tempfile
from pathlib import Path

def test_flask_route_parsing_basic():
    source = '''
from flask import Flask
app = Flask(__name__)

@app.route("/hello")
def hello():
    """Say hello"""
    return "Hello"
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = Path(tmpdir) / "app.py"
        app_path.write_text(source)

        routes = parser.parse_api(tmpdir)

        assert len(routes) == 1
        route = routes[0]
        assert route["method"] == "GET"
        assert route["path"] == "/hello"
        assert route["description"] == "Say hello"


def test_flask_route_with_methods():
    source = '''
from flask import Flask
app = Flask(__name__)

@app.route("/submit", methods=["POST", "PUT"])
def submit():
    """Submit data"""
    return "Done"
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = Path(tmpdir) / "app.py"
        app_path.write_text(source)

        routes = parser.parse_api(tmpdir)

        assert len(routes) == 2  # One for POST, one for PUT
        methods = {r["method"] for r in routes}
        assert methods == {"POST", "PUT"}
        for r in routes:
            assert r["path"] == "/submit"
            assert r["description"] == "Submit data"
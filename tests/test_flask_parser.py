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

def test_flask_blueprint_route():
    source = '''
from flask import Blueprint

bp = Blueprint("auth", __name__)

@bp.route("/login", methods=["POST"])
def login():
    """Login endpoint"""
    return "Logged in"
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        route_path = Path(tmpdir) / "auth.py"
        route_path.write_text(source)

        routes = parser.parse_api(tmpdir)

        assert len(routes) == 1
        route = routes[0]
        assert route["method"] == "POST"
        assert route["path"] == "/login"
        assert route["description"] == "Login endpoint"

def test_flask_route_with_middleware_decorator():
    source = '''
from flask import Flask
app = Flask(__name__)

def login_required(f):
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper

@app.route("/dashboard")
@login_required
def dashboard():
    """Protected dashboard"""
    return "Dashboard"
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "app.py"
        app_file.write_text(source)

        routes = parser.parse_api(tmpdir)

        assert len(routes) == 1
        route = routes[0]
        assert route["method"] == "GET"
        assert route["path"] == "/dashboard"
        assert route["description"] == "Protected dashboard"
        assert "login_required" in route["middlewares"]

def test_flask_route_with_multiple_middlewares():
    source = '''
from flask import Flask
app = Flask(__name__)

def login_required(f): return f
def audit(f): return f

@app.route("/admin")
@login_required
@audit
def admin_panel():
    """Admin panel"""
    return "Admin view"
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = Path(tmpdir) / "admin.py"
        app_path.write_text(source)

        routes = parser.parse_api(tmpdir)

        assert len(routes) == 1
        route = routes[0]
        assert route["method"] == "GET"
        assert route["path"] == "/admin"
        assert route["description"] == "Admin panel"
        assert set(route["middlewares"]) == {"login_required", "audit"}

def test_flask_blueprint_nested():
    source = '''
from flask import Blueprint

bp = Blueprint("test", __name__)

@bp.route("/nested")
def nested_view():
    """Nested route"""
    return "OK"
'''
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = Path(tmpdir) / "routes"
        nested.mkdir()
        (nested / "nested.py").write_text(source)

        routes = parser.parse_api(tmpdir)

        assert any(r["path"] == "/nested" and r["description"] == "Nested route" for r in routes)

def test_flask_decorator_with_args():
    source = '''
from flask import Flask
app = Flask(__name__)

def rate_limit(n):
    def wrapper(f): return f
    return wrapper

@app.route("/limited")
@rate_limit(10)
def limited():
    """Limited route"""
    return "OK"
'''
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.py").write_text(source)
        routes = parser.parse_api(tmpdir)

        r = routes[0]
        assert "rate_limit" in r["middlewares"]

def test_flask_dynamic_route_path():
    source = '''
from flask import Flask
app = Flask(__name__)

@app.route("/user/<int:id>")
def user_profile(id):
    """Get user by ID"""
    return "OK"
'''
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.py").write_text(source)
        routes = parser.parse_api(tmpdir)

        assert routes[0]["path"] == "/user/<int:id>"

def test_flask_param_and_returns_parsing():
    source = '''
from flask import Flask
app = Flask(__name__)

@app.route("/users/<id>", methods=["GET"])
def get_user():
    """
    @summary Fetch a user
    @tags Users
    @param {string} id.path.required - User ID
    @returns {object} 200 - The user object
    @returns {Error} 404 - Not found
    """
    return "user"
    '''
    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = Path(tmpdir) / "app.py"
        app_path.write_text(source)
        routes = parser.parse_api(tmpdir)

        assert len(routes) == 1
        metadata = routes[0]["metadata"]

        assert metadata["tags"] == "Users"
        assert metadata["summary"] == "Fetch a user"
        
        assert isinstance(metadata["param"], list)
        assert metadata["param"][0]["name"] == "id"
        assert metadata["param"][0]["in"] == "path"
        assert metadata["param"][0]["required"] is True

        assert isinstance(metadata["returns"], list)
        codes = {r["statusCode"] for r in metadata["returns"]}
        assert 200 in codes
        assert 404 in codes
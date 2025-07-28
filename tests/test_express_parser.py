import tempfile
from pathlib import Path
from docgen.backends.express import parser

def test_express_basic_routes():
    js_code = """
    const express = require('express');
    const app = express();

    function auth(req, res, next) { next(); }
    function getUsers(req, res) { res.send('Users'); }

    app.get("/users", auth, getUsers);
    app.post("/login", (req, res) => res.send('Login'));
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        app_file = Path(tmpdir) / "app.js"
        app_file.write_text(js_code)

        routes = parser.parse_api(tmpdir)

        assert len(routes) == 2

        user_route = next(r for r in routes if r["path"] == "/users")
        assert user_route["method"] == "GET"
        assert user_route["middlewares"] == ["auth"]

        login_route = next(r for r in routes if r["path"] == "/login")
        assert login_route["method"] == "POST"
        assert login_route["middlewares"] == []


def test_express_nested_directories():
    js_code = """
    const express = require('express');
    const router = express.Router();

    router.get("/profile", (req, res) => res.send('Profile'));

    module.exports = router;
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        nested_dir = Path(tmpdir) / "routes"
        nested_dir.mkdir()
        route_file = nested_dir / "user.js"
        route_file.write_text(js_code)

        routes = parser.parse_api(tmpdir)
        assert any(r["path"] == "/profile" for r in routes)

def test_express_multiple_middlewares():
    source = """
const express = require('express');
const app = express();

function auth(req, res, next) { next(); }
function log(req, res, next) { next(); }
function handler(req, res) { res.send("OK"); }

app.get("/secure", auth, log, handler);
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        route = routes[0]
        assert route["path"] == "/secure"
        assert set(route["middlewares"]) == {"auth", "log"}

def test_express_router_chain():
    source = """
const express = require('express');
const router = express.Router();

function getHandler(req, res) { res.send("GET"); }
function postHandler(req, res) { res.send("POST"); }

router.route("/resource")
  .get(getHandler)
  .post(postHandler);
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "routes.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        methods = {r["method"] for r in routes}
        assert methods == {"GET", "POST"}
        assert all(r["path"] == "/resource" for r in routes)

def test_express_with_jsdoc_comment():
    source = """
const express = require('express');
const app = express();

/**
 * Returns current user info
 */
app.get("/me", (req, res) => res.send("Me"));
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "me.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        route = routes[0]
        assert route["description"].strip() == "Returns current user info"

def test_express_dynamic_path():
    source = """
const express = require('express');
const app = express();

app.get("/user/:id", (req, res) => res.send("User"));
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        assert routes[0]["path"] == "/user/:id"
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

def test_express_jsdoc_tags_and_summary():
    source = """
const express = require('express');
const app = express();

/**
 * @tags Users
 * @summary Get current user
 * Returns current user info.
 */
app.get("/me", (req, res) => res.send("Me"));
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        assert len(routes) == 1
        route = routes[0]

        assert route["method"] == "GET"
        assert route["path"] == "/me"
        assert "Returns current user info" in route["description"]

        assert "metadata" in route
        assert route["metadata"]["tags"] == "Users"
        assert route["metadata"]["summary"] == "Get current user"

def test_express_jsdoc_multiline_description():
    source = """
const express = require('express');
const app = express();

/**
 * @tags Auth
 * @summary Login
 * This route handles login.
 * It validates user credentials and returns a token.
 */
app.post("/login", (req, res) => res.send("Login"));
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        route = routes[0]
        desc = route["description"]

        assert "handles login" in desc
        assert "returns a token" in desc
        assert route["metadata"]["tags"] == "Auth"
        assert route["metadata"]["summary"] == "Login"

def test_express_param_parsing_structured():
    source = """
    const express = require('express');
    const app = express();

    /**
     * @param {string} id.path.required - User ID
     * @param {object} body.body - Request payload
     */
    app.post("/users/:id", (req, res) => res.send("ok"));
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        assert len(routes) == 1
        metadata = routes[0].get("metadata", {})
        assert "param" in metadata
        assert isinstance(metadata["param"], list)
        assert metadata["param"][0]["name"] == "id"
        assert metadata["param"][0]["in"] == "path"
        assert metadata["param"][0]["required"] is True
        assert metadata["param"][0]["type"] == "string"
        assert metadata["param"][0]["description"] == "User ID"

def test_express_returns_parsing_structured():
    source = """
    const express = require('express');
    const app = express();

    /**
     * @returns {object} 200 - Success response
     * @returns {Error} 404 - User not found
     */
    app.get("/users/:id", (req, res) => res.send("ok"));
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        assert len(routes) == 1
        metadata = routes[0].get("metadata", {})
        assert "returns" in metadata
        assert isinstance(metadata["returns"], list)

        return_200 = next((r for r in metadata["returns"] if r["statusCode"] == 200), None)
        return_404 = next((r for r in metadata["returns"] if r["statusCode"] == 404), None)

        assert return_200 is not None
        assert return_200["type"] == "object"
        assert "Success" in return_200["description"]

        assert return_404 is not None
        assert return_404["type"] == "Error"
        assert "not found" in return_404["description"].lower()
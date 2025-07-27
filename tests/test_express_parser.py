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

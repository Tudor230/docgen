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

        assert routes[0]["path"] == "/user/{id}"

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

def test_express_chained_routes_with_comments():
    """Test that chained routes properly associate comments with each method"""
    source = """
const express = require('express');
const router = express.Router();

/**
 * Product management endpoints
 * @tags Products, Inventory, Catalog
 * @summary Manage product catalog
 * @description Complete CRUD operations for product management
 * @param {string} category.query - Filter by product category
 * @param {boolean} active.query - Filter by active status
 * @returns {array} 200 - Array of products
 * @example GET /api/products?category=electronics&active=true
 * @cache 5 minutes
 * @ratelimit 100 requests per minute
 * @version 2.1.0
 */
router
  .route("/products")
  .get((req, res) => {
    res.json({ products: [] });
  })
  /**
   * Create new product
   * @tags Products, Admin
   * @param {string} name.body.required - Product name
   * @param {number} price.body.required - Product price
   * @param {string} category.body.required - Product category
   * @param {string} description.body - Product description
   * @returns {object} 201 - Product created
   * @example POST /api/products
   * @example {"name": "Widget", "price": 29.99, "category": "gadgets"}
   * @validation Requires admin role
   * @audit Product creation logged
   */
  .post((req, res) => {
    res.json({ message: "Product created" });
  });
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "routes.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        # Should have exactly 2 routes (no duplicates)
        assert len(routes) == 2
        
        # Both routes should have the same path
        assert all(r["path"] == "/products" for r in routes)
        
        # Should have one GET and one POST
        methods = {r["method"] for r in routes}
        assert methods == {"GET", "POST"}
        
        # Get specific routes
        get_route = next(r for r in routes if r["method"] == "GET")
        post_route = next(r for r in routes if r["method"] == "POST")
        
        # Test GET route has the first comment's metadata
        assert get_route["description"] == "Product management endpoints"
        assert get_route["metadata"]["tags"] == "Products, Inventory, Catalog"
        assert get_route["metadata"]["summary"] == "Manage product catalog"
        assert get_route["metadata"]["description"] == "Complete CRUD operations for product management"
        assert get_route["metadata"]["cache"] == "5 minutes"
        assert get_route["metadata"]["version"] == "2.1.0"
        
        # GET route should have query parameters
        get_params = get_route["metadata"]["param"]
        assert len(get_params) == 2
        category_param = next(p for p in get_params if p["name"] == "category")
        active_param = next(p for p in get_params if p["name"] == "active")
        assert category_param["in"] == "query"
        assert category_param["type"] == "string"
        assert active_param["in"] == "query"
        assert active_param["type"] == "boolean"
        
        # Test POST route has the second comment's metadata
        assert post_route["description"] == "Create new product"
        assert post_route["metadata"]["tags"] == "Products, Admin"
        assert post_route["metadata"]["validation"] == "Requires admin role"
        assert post_route["metadata"]["audit"] == "Product creation logged"
        
        # POST route should have body parameters
        post_params = post_route["metadata"]["param"]
        assert len(post_params) == 4
        name_param = next(p for p in post_params if p["name"] == "name")
        price_param = next(p for p in post_params if p["name"] == "price")
        assert name_param["in"] == "body"
        assert name_param["required"] is True
        assert price_param["in"] == "body"
        assert price_param["type"] == "number"

def test_express_chained_routes_no_duplication():
    """Test that chained routes without comments don't create duplicates"""
    source = """
const express = require('express');
const router = express.Router();

router
  .route("/api/items")
  .get((req, res) => res.json({ items: [] }))
  .post((req, res) => res.json({ message: "Created" }))
  .put((req, res) => res.json({ message: "Updated" }));
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "routes.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        # Should have exactly 3 routes (no duplicates)
        assert len(routes) == 3
        
        # All routes should have the same path
        assert all(r["path"] == "/api/items" for r in routes)
        
        # Should have GET, POST, and PUT
        methods = {r["method"] for r in routes}
        assert methods == {"GET", "POST", "PUT"}
        
        # All routes should have empty descriptions since no comments
        assert all(r["description"] == "" for r in routes)
        assert all(r["metadata"] == {} for r in routes)

def test_express_chained_routes_with_path_parameters():
    """Test chained routes with path parameters"""
    source = """
const express = require('express');
const router = express.Router();

/**
 * User management
 * @param {string} id.path.required - User ID  
 */
router
  .route("/users/:id")
  .get((req, res) => res.json({ user: req.params.id }))
  /**
   * Update user
   * @param {string} name.body - User name
   */
  .put((req, res) => res.json({ updated: true }));
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "routes.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        assert len(routes) == 2
        assert all(r["path"] == "/users/{id}" for r in routes)
        
        # Both routes should have the path parameter
        for route in routes:
            path_params = [p for p in route["metadata"].get("param", []) if p["in"] == "path"]
            assert len(path_params) == 1
            assert path_params[0]["name"] == "id"
            assert path_params[0]["required"] is True

def test_express_chained_routes_mixed_with_regular():
    """Test file with both chained and regular routes"""
    source = """
const express = require('express');
const router = express.Router();

/**
 * Regular route
 */
router.get("/regular", (req, res) => res.json({ type: "regular" }));

/**
 * First chained route
 */
router
  .route("/chained")
  .get((req, res) => res.json({ type: "chained-get" }))
  /**
   * Second chained route  
   */
  .post((req, res) => res.json({ type: "chained-post" }));

/**
 * Another regular route
 */
router.delete("/another", (req, res) => res.json({ type: "another" }));
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "routes.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        assert len(routes) == 4
        
        # Regular routes
        regular_route = next(r for r in routes if r["path"] == "/regular")
        another_route = next(r for r in routes if r["path"] == "/another")
        assert regular_route["description"] == "Regular route"
        assert another_route["description"] == "Another regular route"
        
        # Chained routes
        chained_get = next(r for r in routes if r["path"] == "/chained" and r["method"] == "GET")
        chained_post = next(r for r in routes if r["path"] == "/chained" and r["method"] == "POST")
        assert chained_get["description"] == "First chained route"
        assert chained_post["description"] == "Second chained route"

def test_express_chained_routes_with_middlewares():
    """Test chained routes with middleware functions"""
    source = """
const express = require('express');
const router = express.Router();

function auth(req, res, next) { next(); }
function validate(req, res, next) { next(); }

/**
 * Protected endpoints
 */
router
  .route("/protected")
  .get(auth, (req, res) => res.json({ data: "secret" }))
  /**
   * Create protected resource
   */
  .post(auth, validate, (req, res) => res.json({ created: true }));
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "routes.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        assert len(routes) == 2
        
        get_route = next(r for r in routes if r["method"] == "GET")
        post_route = next(r for r in routes if r["method"] == "POST")
        
        assert get_route["middlewares"] == ["auth"]
        assert post_route["middlewares"] == ["auth", "validate"]

def test_express_chained_routes_malformed_comments():
    """Test graceful handling of malformed JSDoc comments"""
    source = """
const express = require('express');
const router = express.Router();

/**
 * Missing closing tag
 * @param {string name - Malformed param
 */
router
  .route("/test")
  .get((req, res) => res.json({}))
  /**
   * @invalidtag This is not a real tag
   * @param - Missing type and name
   */
  .post((req, res) => res.json({}));
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "routes.js").write_text(source)
        routes = parser.parse_api(tmpdir)

        # Should still parse routes even with malformed comments
        assert len(routes) == 2
        assert all(r["path"] == "/test" for r in routes)
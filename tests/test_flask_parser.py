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


def test_flask_multiple_methods_with_separate_documentation():
    """Test Flask routes with multiple methods documented separately"""
    source = '''
from flask import Flask
app = Flask(__name__)

@app.route("/products", methods=["GET"])
def get_products():
    """
    Product management endpoints
    
    @tags Products, Inventory, Catalog
    @summary Get product catalog
    @description Retrieve all products with filtering options
    @param {string} category.query - Filter by product category
    @param {boolean} active.query - Filter by active status
    @returns {array} 200 - Array of products
    @example GET /products?category=electronics&active=true
    @cache 5 minutes
    @version 2.1.0
    """
    return {"products": []}

@app.route("/products", methods=["POST"])
def create_product():
    """
    Create new product
    
    @tags Products, Admin
    @summary Add new product
    @description Create a new product in the catalog
    @param {string} name.body.required - Product name
    @param {number} price.body.required - Product price
    @param {string} category.body.required - Product category
    @param {string} description.body - Product description
    @returns {object} 201 - Product created successfully
    @example POST /products
    @example {"name": "Widget", "price": 29.99, "category": "gadgets"}
    @validation Requires admin role
    @audit Product creation logged
    """
    return {"message": "Product created"}
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = Path(tmpdir) / "app.py"
        app_path.write_text(source)

        routes = parser.parse_api(tmpdir)

        # Should have exactly 2 routes
        assert len(routes) == 2
        
        # Both routes should have the same path
        assert all(r["path"] == "/products" for r in routes)
        
        # Should have one GET and one POST
        methods = {r["method"] for r in routes}
        assert methods == {"GET", "POST"}
        
        # Get specific routes
        get_route = next(r for r in routes if r["method"] == "GET")
        post_route = next(r for r in routes if r["method"] == "POST")
        
        # Test GET route has correct metadata
        assert "Product management endpoints" in get_route["description"]
        assert get_route["metadata"]["tags"] == "Products, Inventory, Catalog"
        assert get_route["metadata"]["summary"] == "Get product catalog"
        assert get_route["metadata"]["description"] == "Retrieve all products with filtering options"
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
        
        # Test POST route has correct metadata
        assert "Create new product" in post_route["description"]
        assert post_route["metadata"]["tags"] == "Products, Admin"
        assert post_route["metadata"]["summary"] == "Add new product"
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

def test_flask_same_path_different_methods():
    """Test Flask routes with same path but different methods"""
    source = '''
from flask import Flask
app = Flask(__name__)

@app.route("/api/users", methods=["GET"])
def list_users():
    """Get all users"""
    return {"users": []}

@app.route("/api/users", methods=["POST"])
def create_user():
    """Create a new user"""
    return {"message": "User created"}

@app.route("/api/users", methods=["DELETE"])
def delete_all_users():
    """Delete all users"""
    return {"message": "All users deleted"}
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = Path(tmpdir) / "app.py"
        app_path.write_text(source)

        routes = parser.parse_api(tmpdir)

        # Should have exactly 3 routes
        assert len(routes) == 3
        
        # All routes should have the same path
        assert all(r["path"] == "/api/users" for r in routes)
        
        # Should have GET, POST, and DELETE
        methods = {r["method"] for r in routes}
        assert methods == {"GET", "POST", "DELETE"}
        
        # Each route should have its own description
        get_route = next(r for r in routes if r["method"] == "GET")
        post_route = next(r for r in routes if r["method"] == "POST")
        delete_route = next(r for r in routes if r["method"] == "DELETE")
        
        assert get_route["description"] == "Get all users"
        assert post_route["description"] == "Create a new user"
        assert delete_route["description"] == "Delete all users"

def test_flask_path_parameters_with_types():
    """Test Flask path parameters with different types"""
    source = '''
from flask import Flask
app = Flask(__name__)

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """
    Get user by ID
    @param {integer} user_id.path.required - User ID
    """
    return {"user_id": user_id}

@app.route("/files/<path:filename>", methods=["GET"])
def get_file(filename):
    """
    Get file by path
    @param {string} filename.path.required - File path
    """
    return {"filename": filename}

@app.route("/uuid/<uuid:item_id>", methods=["GET"])
def get_item(item_id):
    """Get item by UUID"""
    return {"item_id": str(item_id)}
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = Path(tmpdir) / "app.py"
        app_path.write_text(source)

        routes = parser.parse_api(tmpdir)

        assert len(routes) == 3
        
        # Test integer path parameter
        user_route = next(r for r in routes if "user_id" in r["path"])
        assert user_route["path"] == "/users/{user_id}"
        user_param = next(p for p in user_route["metadata"]["param"] if p["name"] == "user_id")
        assert user_param["type"] == "integer"
        assert user_param["in"] == "path"
        assert user_param["required"] is True
        
        # Test path parameter
        file_route = next(r for r in routes if "filename" in r["path"])
        assert file_route["path"] == "/files/{filename}"
        file_param = next(p for p in file_route["metadata"]["param"] if p["name"] == "filename")
        assert file_param["type"] == "string"
        
        # Test UUID parameter
        uuid_route = next(r for r in routes if "item_id" in r["path"])
        assert uuid_route["path"] == "/uuid/{item_id}"
        uuid_param = next(p for p in uuid_route["metadata"]["param"] if p["name"] == "item_id")
        assert uuid_param["type"] == "string"
        assert uuid_param.get("format") == "uuid"

def test_flask_blueprint_with_url_prefix():
    """Test Flask blueprint routes with URL prefix"""
    source = '''
from flask import Flask, Blueprint
app = Flask(__name__)

api = Blueprint("api", __name__, url_prefix="/api/v1")

@api.route("/users", methods=["GET"])
def list_users():
    """List all users from API v1"""
    return {"users": []}

@api.route("/users", methods=["POST"])
def create_user():
    """Create user in API v1"""
    return {"created": True}

app.register_blueprint(api)
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = Path(tmpdir) / "app.py"
        app_path.write_text(source)

        routes = parser.parse_api(tmpdir)

        assert len(routes) == 2
        
        # Blueprint routes should be detected (even if URL prefix isn't applied in parsing)
        assert all(r["path"] == "/users" for r in routes)
        
        get_route = next(r for r in routes if r["method"] == "GET")
        post_route = next(r for r in routes if r["method"] == "POST")
        
        assert "API v1" in get_route["description"]
        assert "API v1" in post_route["description"]

def test_flask_malformed_docstrings():
    """Test graceful handling of malformed docstrings"""
    source = '''
from flask import Flask
app = Flask(__name__)

@app.route("/test1", methods=["GET"])
def test_no_docstring():
    # No docstring at all
    return {"test": 1}

@app.route("/test2", methods=["GET"])
def test_malformed_tags():
    """
    Valid description
    @invalidtag This tag doesn't exist
    @param - Missing parameter info
    @returns - Missing return info
    """
    return {"test": 2}

@app.route("/test3", methods=["GET"])
def test_empty_docstring():
    """"""
    return {"test": 3}
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = Path(tmpdir) / "app.py"
        app_path.write_text(source)

        routes = parser.parse_api(tmpdir)

        # Should still parse all routes despite malformed docstrings
        assert len(routes) == 3
        
        # Routes should have appropriate descriptions
        test1 = next(r for r in routes if r["path"] == "/test1")
        test2 = next(r for r in routes if r["path"] == "/test2")
        test3 = next(r for r in routes if r["path"] == "/test3")
        
        assert test1["description"] == ""  # No docstring
        assert "Valid description" in test2["description"]  # Should extract valid parts
        assert test3["description"] == ""  # Empty docstring

def test_flask_complex_metadata_parsing():
    """Test complex Flask docstring metadata parsing"""
    source = '''
from flask import Flask
app = Flask(__name__)

@app.route("/complex", methods=["POST"])
def complex_endpoint():
    """
    Complex endpoint with many metadata tags
    
    This endpoint demonstrates comprehensive metadata parsing
    with multiple lines and various tag types.
    
    @tags API, Complex, Testing
    @summary Complex test endpoint
    @description A comprehensive test of metadata parsing capabilities
    @param {string} name.body.required - User's full name
    @param {integer} age.body - User's age (optional)
    @param {string} email.body.required - User's email address
    @param {array} tags.body - Array of user tags
    @returns {object} 201 - Successfully created user
    @returns {object} 400 - Validation error occurred
    @returns {object} 409 - User already exists
    @example POST /complex
    @example {"name": "John Doe", "age": 30, "email": "john@example.com"}
    @throws ValidationError When input data is invalid
    @throws ConflictError When user already exists
    @author Test Suite
    @since v2.1.0
    @version 1.0.0
    @deprecated Use /v2/complex instead
    @security Bearer token required
    @ratelimit 10 requests per minute
    @cache No caching
    """
    return {"message": "Complex endpoint"}
'''

    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = Path(tmpdir) / "app.py"
        app_path.write_text(source)

        routes = parser.parse_api(tmpdir)

        assert len(routes) == 1
        route = routes[0]
        
        # Check description
        assert "Complex endpoint with many metadata tags" in route["description"]
        assert "comprehensive test" in route["description"]
        
        # Check metadata
        metadata = route["metadata"]
        assert metadata["tags"] == "API, Complex, Testing"
        assert metadata["summary"] == "Complex test endpoint"
        assert metadata["author"] == "Test Suite"
        assert metadata["since"] == "v2.1.0"
        assert metadata["deprecated"] == "Use /v2/complex instead"
        assert metadata["security"] == "Bearer token required"
        
        # Check parameters
        params = metadata["param"]
        assert len(params) == 4
        
        name_param = next(p for p in params if p["name"] == "name")
        age_param = next(p for p in params if p["name"] == "age")
        
        assert name_param["required"] is True
        assert name_param["type"] == "string"
        assert age_param["required"] is False
        assert age_param["type"] == "integer"
        
        # Check returns
        returns = metadata["returns"]
        assert len(returns) == 3
        success_return = next(r for r in returns if r["statusCode"] == 201)
        assert success_return["description"] == "Successfully created user"

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

        assert routes[0]["path"] == "/user/{id}"

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
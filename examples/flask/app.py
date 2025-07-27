from flask import Flask
app = Flask(__name__)

@app.route("/users", methods=["GET"])
def get_users():
    """Get list of users"""
    return "List of users"

@app.route("/users", methods=["POST"])
def create_user():
    """Create a new user"""
    return "User created"

from flask import Flask

def create_app():
    """Create and configure the Flask application and register blueprints."""
    app = Flask(__name__)

    # Import and register routes (delayed import to avoid circulars)
    from .routes import register_routes
    register_routes(app)

    return app

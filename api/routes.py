def register_routes(app):
    # Register API blueprints
    from .controllers.diagnose_controller import bp as diagnose_bp

    app.register_blueprint(diagnose_bp)

    from .controllers import diagnose_controller

    app.add_url_rule("/ingest", endpoint="legacy_ingest", view_func=diagnose_controller.ingest_route, methods=["POST"])
    app.add_url_rule("/diagnose", endpoint="legacy_diagnose", view_func=diagnose_controller.diagnose, methods=["POST"])

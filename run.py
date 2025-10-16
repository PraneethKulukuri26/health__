import os

# Prefer the new package app factory
try:
    from api import create_app

    app = create_app()
except Exception:
    # try:
    #     from rag_pipeline import app as legacy_app

    #     app = legacy_app
    # except Exception:
    #     raise
    raise


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port, debug=True)

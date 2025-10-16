from flask import Blueprint, request, jsonify, Response, stream_with_context
from ..services.rag_service import ingest_dataset_stream, query_disease
import os

bp = Blueprint("diagnose", __name__, url_prefix="/api")


@bp.route("/ingest", methods=["POST"])
def ingest_route():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    upload_dir = os.environ.get("UPLOAD_DIR", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)

    # def gen():
    #     for item in ingest_dataset_stream(file_path):
    #         yield f"data: {jsonify(item).get_data(as_text=True)}\n\n"

    return Response(ingest_dataset_stream(file_path), mimetype="text/event-stream")


@bp.route("/diagnose", methods=["POST"])
def diagnose():
    data = request.get_json() or {}
    user_query = data.get("query", "")
    if not user_query:
        return jsonify({"error": "Missing query"}), 400

    result = query_disease(user_query)
    return jsonify(result)

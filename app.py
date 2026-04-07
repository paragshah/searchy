import csv
import io

from flask import Flask, request, jsonify, render_template, Response
from db import init_db
from config import PORT, HOST
import models
from bookmark_parser import parse_bookmark_html

app = Flask(__name__)


# --- Pages ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


@app.route("/bookmarklet")
def bookmarklet_page():
    return render_template("bookmarklet.html", port=PORT)


@app.route("/bookmarklet/add")
def bookmarklet_popup():
    url = request.args.get("url", "")
    title = request.args.get("title", "")
    return render_template("bookmarklet_popup.html", url=url, title=title)


# --- Search API ---

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    mode = request.args.get("mode", "and")
    if not q:
        return jsonify([])
    results = models.search_links(q, mode=mode)
    return jsonify(results)


# --- Links CRUD ---

@app.route("/api/links", methods=["GET"])
def api_list_links():
    sort_by = request.args.get("sort_by", "url")
    order = request.args.get("order", "asc")
    return jsonify(models.list_links(sort_by=sort_by, order=order))


@app.route("/api/links", methods=["POST"])
def api_create_link():
    data = request.get_json()
    if not data or not data.get("url"):
        return jsonify({"error": "URL is required"}), 400

    url = data["url"].strip()
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    try:
        link = models.create_link(url, title=title, description=description, tags=tags)
        return jsonify(link), 201
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            return jsonify({"error": "URL already exists"}), 409
        return jsonify({"error": str(e)}), 500


@app.route("/api/links/<int:link_id>", methods=["PUT"])
def api_update_link(link_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    url = data.get("url")
    title = data.get("title")
    description = data.get("description")
    tags = data.get("tags")
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    try:
        link = models.update_link(link_id, url=url, title=title, description=description, tags=tags)
        if not link:
            return jsonify({"error": "Link not found"}), 404
        return jsonify(link)
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            return jsonify({"error": "URL already exists"}), 409
        return jsonify({"error": str(e)}), 500


@app.route("/api/links/<int:link_id>", methods=["DELETE"])
def api_delete_link(link_id):
    if models.delete_link(link_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Link not found"}), 404


# --- Click tracking ---

@app.route("/api/links/<int:link_id>/click", methods=["POST"])
def api_record_click(link_id):
    if models.record_click(link_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Link not found"}), 404


@app.route("/api/history")
def api_history():
    return jsonify(models.get_recent_clicks())


# --- Clear database ---

@app.route("/api/clear", methods=["POST"])
def api_clear():
    models.clear_all()
    return jsonify({"ok": True})


# --- Import / Export ---

@app.route("/api/import/parse", methods=["POST"])
def api_import_parse():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename or ""
    content = file.read().decode("utf-8", errors="ignore")

    if filename.lower().endswith(".csv"):
        bookmarks = []
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            url = (row.get("Links") or row.get("links") or "").strip()
            if not url:
                continue
            title = (row.get("Title") or row.get("title") or "").strip()
            description = (row.get("Description") or row.get("description") or "").strip()
            tags_raw = (row.get("Tags") or row.get("tags") or "").strip()
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            bookmarks.append({
                "url": url,
                "title": title,
                "description": description,
                "tags": tags,
            })
    else:
        bookmarks = parse_bookmark_html(content)

    return jsonify(bookmarks)


@app.route("/api/import/save", methods=["POST"])
def api_import_save():
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"error": "Expected a list of bookmarks"}), 400

    count = models.bulk_import(data)
    return jsonify({"imported": count})


@app.route("/api/export")
def api_export():
    fmt = request.args.get("format", "json")
    if fmt == "csv":
        return Response(
            models.export_csv(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=searchy_export.csv"},
        )
    return Response(
        models.export_json(),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=searchy_export.json"},
    )


# --- Bookmarklet ---

@app.route("/api/bookmarklet", methods=["POST", "OPTIONS"])
def api_bookmarklet():
    if request.method == "OPTIONS":
        resp = jsonify({"ok": True})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    data = request.get_json()
    if not data or not data.get("url"):
        resp = jsonify({"error": "URL is required"})
        resp.status_code = 400
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    url = data["url"].strip()
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    try:
        link = models.create_link(url, title=title, description=description, tags=tags)
        resp = jsonify(link)
        resp.status_code = 201
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            resp = jsonify({"error": "URL already exists"})
            resp.status_code = 409
        else:
            resp = jsonify({"error": str(e)})
            resp.status_code = 500

    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


if __name__ == "__main__":
    import os
    init_db()
    debug = os.isatty(0)
    app.run(host=HOST, port=PORT, debug=debug, use_reloader=debug)

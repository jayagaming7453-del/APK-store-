from flask import Flask, render_template, send_from_directory, jsonify
import json, os

app = Flask(__name__)

def load_apks():
    if os.path.exists("apks.json"):
        with open("apks.json") as f:
            return json.load(f)
    return []

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/apks")
def api_apks():
    apks = load_apks()
    # Convert file paths to URLs
    result = []
    for apk in apks:
        result.append({
            "id": apk["id"],
            "name": apk["name"],
            "badge": apk.get("badge", ""),
            "tg": apk.get("tg", ""),
            "support": apk.get("support", ""),
            "video": apk.get("video", ""),
            "file_name": apk["file_name"],
            "date": apk["date"],
            "img_url": "/" + apk["img_path"] if apk.get("img_path") else "",
            "apk_url": "/" + apk["apk_path"]
        })
    return jsonify(result)

@app.route("/static/apks/<filename>")
def serve_apk(filename):
    return send_from_directory("static/apks", filename, as_attachment=True)

@app.route("/static/imgs/<filename>")
def serve_img(filename):
    return send_from_directory("static/imgs", filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

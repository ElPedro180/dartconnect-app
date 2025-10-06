from flask import Flask, render_template, send_file
import subprocess
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run")
def run_scraper():
    subprocess.run(["python", "dart_scraper.py"])
    return "✅ Scraper executed!"

@app.route("/download")
def download_csv():
    path = "dart_highlights_combined.csv"
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "❌ CSV not found."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
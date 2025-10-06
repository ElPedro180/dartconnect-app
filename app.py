from flask import Flask, render_template
import asyncio
import os

from dart_scraper import main as run_dart_script

app = Flask(__name__)

@app.route("/")
def index():
    csv_file = "dart_highlights_combined.csv"
    if os.path.exists(csv_file):
        with open(csv_file, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        lines = ["No data yet — the automatic job runs every Tuesday at 00:01 UTC."]
    return render_template("index.html", lines=lines)

@app.route("/run")
def run_now():
    asyncio.run(run_dart_script())
    return "✅ Script executed manually! Reload the page to see updated results."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

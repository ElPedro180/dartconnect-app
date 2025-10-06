from flask import Flask, render_template
import subprocess
import csv
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/run")
def run_scraper():
    subprocess.run(["python", "dart_scraper.py"])
    return render_template("index.html", message="✅ Scraper executed!")

@app.route("/results")
def show_results():
    csv_path = "dart_highlights_combined.csv"
    if not os.path.exists(csv_path):
        return render_template("index.html", message="❌ CSV not found.")

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)

    return render_template("index.html", headers=headers, rows=rows)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Zeeploy provides PORT dynamically
    app.run(host="0.0.0.0", port=port)
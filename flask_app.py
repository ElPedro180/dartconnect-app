from flask import Flask, render_template, jsonify
import asyncio
import dart_scraper

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scrape", methods=["POST"])
def scrape():
    try:
        results = asyncio.run(dart_scraper.run_scraper())
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
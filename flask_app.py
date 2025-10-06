from flask import Flask, render_template, jsonify
import subprocess

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/scrape", methods=["POST"])
def scrape():
    try:
        # Example: run your scraper script
        result = subprocess.check_output(["python", "scripts/scrape_darts.py"], text=True)
        return jsonify({"status": "success", "output": result})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "output": e.output}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
#!/usr/bin/env python3
"""Simple shared leaderboard API for Dragon Maze. Deploy anywhere."""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json, os, time, threading

app = Flask(__name__)
CORS(app)  # Allow requests from any origin (GitHub Pages)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_leaderboard.json")
lock = threading.Lock()


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


@app.route("/api/leaderboard", methods=["GET"])
def get_leaderboard():
    """Get all leaderboards."""
    return jsonify(load_data())


@app.route("/api/leaderboard/<board_key>", methods=["GET"])
def get_board(board_key):
    """Get leaderboard for a specific maze size."""
    data = load_data()
    return jsonify(data.get(board_key, []))


@app.route("/api/leaderboard/<board_key>", methods=["POST"])
def add_entry(board_key):
    """Add a score. Body: {name, time, moves}"""
    entry = request.get_json()
    if not entry or "name" not in entry or "time" not in entry or "moves" not in entry:
        return jsonify({"error": "Need name, time, moves"}), 400

    # Sanitise
    name = str(entry["name"])[:15].strip()
    try:
        t = round(float(entry["time"]), 2)
        m = int(entry["moves"])
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid time/moves"}), 400

    if not name or t < 0 or m < 0:
        return jsonify({"error": "Invalid data"}), 400

    with lock:
        data = load_data()
        if board_key not in data:
            data[board_key] = []
        data[board_key].append({"name": name, "time": t, "moves": m})
        data[board_key].sort(key=lambda e: e["time"])
        data[board_key] = data[board_key][:10]  # top 10 only
        save_data(data)

    return jsonify({"ok": True, "rank": next(
        (i+1 for i, e in enumerate(data[board_key]) if e["name"] == name and e["time"] == t), None
    )})


if __name__ == "__main__":
    print("Dragon Maze Leaderboard API running on port 5555")
    app.run(host="0.0.0.0", port=5555)

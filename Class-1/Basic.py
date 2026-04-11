"""
Rumor: Social Deduction Game
Author: Your Name
Platform: Raspberry Pi 4B, Ubuntu
Goal: Players spread and investigate rumors, gain reputation points.
Scoring prioritizes sneaky/socially manipulative players first, honest players second.
"""

import os
import random
import sqlite3
import time
from flask import Flask, render_template, request, redirect, url_for, g
from werkzeug.utils import secure_filename

# =====================================================
# CONFIG
# =====================================================
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "static/uploads"
app.config['DATABASE'] = "game.db"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
ROUND_DURATION = 75  # seconds

# =====================================================
# DATABASE
# =====================================================
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db:
        db.close()

def init_db():
    db = get_db()
    # Players table
    db.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            gender TEXT,
            role TEXT,
            reputation INTEGER DEFAULT 50,
            influence INTEGER DEFAULT 10,
            acted_this_round INTEGER DEFAULT 0,
            image TEXT,
            snake_score INTEGER DEFAULT 0,
            honesty_score INTEGER DEFAULT 0
        )
    """)
    # Rumors table
    db.execute("""
        CREATE TABLE IF NOT EXISTS rumors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            truth TEXT,
            tier TEXT,
            target INTEGER,
            spread_count INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1
        )
    """)
    # Game state
    db.execute("""
        CREATE TABLE IF NOT EXISTS game_state (
            id INTEGER PRIMARY KEY CHECK(id=1),
            phase TEXT DEFAULT 'JOIN',
            round_number INTEGER DEFAULT 1,
            round_end_time INTEGER DEFAULT 0
        )
    """)
    db.execute("INSERT OR IGNORE INTO game_state (id) VALUES (1)")
    db.commit()

# =====================================================
# UTILITY FUNCTIONS
# =====================================================
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def assign_role():
    # Everyone can investigate and spread
    return "Player"

def get_game_state():
    db = get_db()
    return db.execute("SELECT * FROM game_state WHERE id=1").fetchone()

def start_new_round():
    db = get_db()
    end_time = int(time.time()) + ROUND_DURATION
    db.execute("UPDATE players SET acted_this_round=0")
    db.execute("""
        UPDATE game_state
        SET phase='ACTION',
            round_number = round_number + 1,
            round_end_time=?
        WHERE id=1
    """, (end_time,))
    db.commit()

def initialize_rumors():
    db = get_db()
    db.execute("DELETE FROM rumors")
    sample_rumors = [
        ("Maya is hiding a pregnancy.", "Semi-True", "Red", 1),
        ("Sade’s 'flu' is actually morning sickness.", "True", "Red", 2),
        ("Chris is embezzling Dorm funds.", "Semi-True", "Red", 3),
        ("Jordan drugged a freshman at the mixer.", "True", "Red", 4),
        ("Zara’s app tracks movements secretly.", "Semi-True", "Red", 5),
    ]
    for r in sample_rumors:
        db.execute("INSERT INTO rumors (text, truth, tier, target) VALUES (?, ?, ?, ?)", r)
    db.commit()

# =====================================================
# ROUTES
# =====================================================

@app.route("/")
def index():
    db = get_db()
    state = get_game_state()
    current_time = int(time.time())
    remaining_time = max(0, state["round_end_time"] - current_time)

    if state["phase"] == "ACTION" and remaining_time <= 0:
        db.execute("UPDATE game_state SET phase='VOTE' WHERE id=1")
        db.commit()
        state = get_game_state()

    players = db.execute("SELECT * FROM players").fetchall()
    rumors = db.execute("SELECT * FROM rumors WHERE active=1").fetchall()
    return render_template("index.html", players=players, rumors=rumors, state=state, remaining_time=remaining_time)

@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        name = request.form["name"]
        gender = request.form["gender"]
        role = assign_role()

        image_path = None
        file = request.files.get("photo")
        if file and file.filename != "" and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            image_path = path

        db = get_db()
        db.execute("INSERT INTO players (name, gender, role, image) VALUES (?, ?, ?, ?)", (name, gender, role, image_path))
        db.commit()
        return redirect("/")
    return render_template("join.html")

@app.route("/start_game")
def start_game():
    db = get_db()
    initialize_rumors()
    end_time = int(time.time()) + ROUND_DURATION
    db.execute("UPDATE game_state SET phase='ACTION', round_number=1, round_end_time=?", (end_time,))
    db.commit()
    return redirect("/")

@app.route("/spread/<int:player_id>/<int:rumor_id>")
def spread(player_id, rumor_id):
    db = get_db()
    state = get_game_state()
    if state["phase"] != "ACTION":
        return "Actions locked."

    player = db.execute("SELECT * FROM players WHERE id=?", (player_id,)).fetchone()
    rumor = db.execute("SELECT * FROM rumors WHERE id=?", (rumor_id,)).fetchone()
    if not player or not rumor:
        return "Invalid."

    if player["acted_this_round"]:
        return "Already acted."

    db.execute("UPDATE rumors SET spread_count = spread_count + 1 WHERE id=?", (rumor_id,))
    db.execute("UPDATE players SET influence = influence + 2, acted_this_round=1 WHERE id=?", (player_id,))
    db.commit()
    return redirect("/")

@app.route("/investigate/<int:player_id>/<int:rumor_id>")
def investigate(player_id, rumor_id):
    db = get_db()
    state = get_game_state()
    if state["phase"] != "ACTION":
        return "Actions locked."

    player = db.execute("SELECT * FROM players WHERE id=?", (player_id,)).fetchone()
    rumor = db.execute("SELECT * FROM rumors WHERE id=?", (rumor_id,)).fetchone()
    if not player or not rumor:
        return "Invalid."

    if player["acted_this_round"]:
        return "Already acted."

    chance = player["influence"] + random.randint(0, 40)
    if rumor["truth"] == "False" and chance > 60:
        db.execute("UPDATE rumors SET active=0 WHERE id=?", (rumor_id,))
    db.execute("UPDATE players SET acted_this_round=1 WHERE id=?", (player_id,))
    db.commit()
    return redirect("/")

@app.route("/vote", methods=["GET", "POST"])
def vote():
    db = get_db()
    state = get_game_state()
    if state["phase"] != "VOTE":
        return "Voting not allowed."

    players = db.execute("SELECT * FROM players").fetchall()
    rumors = db.execute("SELECT * FROM rumors").fetchall()

    if request.method == "POST":
        # Example: form sends rumor votes and most honest vote
        for player in players:
            snake_points = int(request.form.get(f'snake_{player["id"]}', 0))
            honest_points = int(request.form.get(f'honest_{player["id"]}', 0))
            db.execute("UPDATE players SET snake_score = ?, honesty_score = ? WHERE id=?", (snake_points, honest_points, player["id"]))
        # Redistribute points based on snake priority
        total_points = sum(p["reputation"] for p in players)
        # prioritize snake_score transfers
        for p in players:
            p_snake = p["snake_score"]
            p_honest = p["honesty_score"]
            p_rep = p["reputation"]
            # Example simple redistribution
            p_new = p_rep + p_snake + p_honest
            db.execute("UPDATE players SET reputation=? WHERE id=?", (p_new, p["id"]))
        db.execute("UPDATE game_state SET phase='ACTION' WHERE id=1")
        db.commit()
        start_new_round()
        return redirect("/")

    return render_template("vote.html", players=players, rumors=rumors)

@app.route("/next_round")
def next_round():
    start_new_round()
    return redirect("/")

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)




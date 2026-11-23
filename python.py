from flask import Flask, request, jsonify, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "tulu-heritage-demo-secret-key"
)

DATABASE = "heritage.db"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def initialize_db():

    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Temples table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS temples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            deity TEXT,
            famous TEXT,
            history TEXT,
            image TEXT,
            model_3d TEXT
        )
    """)

    # Add extra columns to an older database
    existing_columns = {
        row["name"]
        for row in cursor.execute(
            "PRAGMA table_info(temples)"
        ).fetchall()
    }

    extra_columns = {
        "architecture": "TEXT",
        "festivals": "TEXT",
        "significance": "TEXT"
    }

    for column, datatype in extra_columns.items():
        if column not in existing_columns:
            cursor.execute(
                f"ALTER TABLE temples ADD COLUMN {column} {datatype}"
            )

    # ======================================
    # TEN FAMOUS TEMPLES
    # ======================================

    temple_data = [

        (
            "Shree Rajarajeshwari Temple",
            "Polali, Bantwal",
            "Goddess Rajarajeshwari",
            "Famous for its traditional worship and annual Polali festival.",
            "An important historic temple in the Polali region.",
            "",
            "",
            "Traditional coastal Karnataka temple architecture.",
            "Annual Polali Jaatre.",
            "An important centre of local religious heritage."
        ),

        (
            "Kukke Sri Subrahmanya Temple",
            "Subrahmanya, Kadaba",
            "Lord Subrahmanya",
            "Famous for its pilgrimage traditions and worship of Lord Subrahmanya.",
            "A well-known pilgrimage centre near the Western Ghats.",
            "",
            "",
            "Traditional temple architecture.",
            "Annual religious festivals and special poojas.",
            "An important pilgrimage destination."
        ),

        (
            "Sri Kshetra Dharmasthala",
            "Dharmasthala, Belthangady",
            "Lord Manjunatha",
            "Famous for religious service, charity and hospitality.",
            "A historic religious centre known for community service.",
            "",
            "",
            "Traditional temple architecture.",
            "Laksha Deepotsava and other religious festivals.",
            "Known for charity, education and community welfare."
        ),

        (
            "Kateel Sri Durgaparameshwari Temple",
            "Kateel, Mangaluru",
            "Goddess Durgaparameshwari",
            "Famous for its location on the Nandini River.",
            "An important pilgrimage centre dedicated to Goddess Durgaparameshwari.",
            "",
            "",
            "Traditional temple structures near the river.",
            "Annual temple festivals and Yakshagana traditions.",
            "An important Shakti worship centre."
        ),

        (
            "Kadri Sri Manjunatha Temple",
            "Kadri, Mangaluru",
            "Lord Manjunatha",
            "Known for its historic temple and ancient sculptures.",
            "One of the historically significant religious places in Mangaluru.",
            "",
            "",
            "Traditional temple architecture with historic features.",
            "Annual Jaatre and religious celebrations.",
            "Important to the cultural history of Mangaluru."
        ),

        (
            "Mangaladevi Temple",
            "Bolar, Mangaluru",
            "Goddess Mangaladevi",
            "Associated with the name and history of Mangaluru.",
            "An important historic shrine in Mangaluru.",
            "",
            "",
            "Traditional coastal Karnataka temple architecture.",
            "Navaratri celebrations.",
            "A major centre of Goddess worship."
        ),

        (
            "Kudroli Gokarnanatheshwara Temple",
            "Kudroli, Mangaluru",
            "Lord Gokarnanatheshwara",
            "Famous for colourful architecture and Mangaluru Dasara.",
            "An important centre of worship and community heritage.",
            "",
            "",
            "Colourful temple architecture and decorative gopurams.",
            "Mangaluru Dasara celebrations.",
            "An important cultural and religious landmark."
        ),

        (
            "Nellitheertha Somanatheshwara Cave Temple",
            "Nellitheertha, Dakshina Kannada",
            "Lord Somanatheshwara",
            "Known for its natural cave and sacred pond.",
            "A temple associated with a natural cave used for religious worship.",
            "",
            "",
            "Natural cave temple setting.",
            "Temple poojas and local religious festivals.",
            "A distinctive natural and spiritual heritage site."
        ),

        (
            "Kudupu Sri Anantha Padmanabha Temple",
            "Kudupu, Mangaluru",
            "Lord Anantha Padmanabha",
            "Known for its serpent worship traditions.",
            "A significant religious destination in the Mangaluru region.",
            "",
            "",
            "Traditional temple architecture.",
            "Religious rituals and annual celebrations.",
            "Important to local religious traditions."
        ),

        (
            "Puttur Sri Mahalingeshwara Temple",
            "Puttur, Dakshina Kannada",
            "Lord Mahalingeshwara",
            "Known for its historic Shiva temple and annual festival.",
            "An important religious landmark in Puttur.",
            "",
            "",
            "Traditional coastal Karnataka temple architecture.",
            "Annual temple Jaatre.",
            "A significant centre of worship and local heritage."
        )

    ]

    # Insert temples only when the table is empty
    cursor.execute("SELECT COUNT(*) FROM temples")
    count = cursor.fetchone()[0]

    if count == 0:

        cursor.executemany("""
            INSERT INTO temples (
                name,
                location,
                deity,
                famous,
                history,
                image,
                model_3d,
                architecture,
                festivals,
                significance
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, temple_data)

    conn.commit()
    conn.close()


# ==========================================
# LOGIN REQUIRED
# ==========================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return jsonify({
                "error": "Please login first"
            }), 401

        return function(*args, **kwargs)

    return wrapper


# ==========================================
# REGISTER API
# ==========================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({
            "error": "All fields are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must contain at least 8 characters"
        }), 400

    hashed_password = generate_password_hash(password)

    conn = get_db()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email, hashed_password))

        user_id = cursor.lastrowid

        conn.commit()

        session.clear()
        session["user_id"] = user_id
        session["user_name"] = name

        return jsonify({
            "message": "Registration successful",
            "name": name
        }), 201

    except sqlite3.IntegrityError:

        return jsonify({
            "error": "Email already registered"
        }), 409

    finally:
        conn.close()


# ==========================================
# LOGIN API
# ==========================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = str(data.get("email", "")).strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Enter email and password"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users WHERE email = ?
    """, (email,))

    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]

        return jsonify({
            "message": "Login successful",
            "name": user["name"]
        })

    return jsonify({
        "error": "Invalid email or password"
    }), 401


# ==========================================
# CHECK LOGIN API
# ==========================================

@app.route("/api/me", methods=["GET"])
def me():

    if "user_id" in session:

        return jsonify({
            "logged_in": True,
            "name": session.get("user_name")
        })

    return jsonify({
        "logged_in": False
    })


# ==========================================
# LOGOUT API
# ==========================================

@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "message": "Logout successful"
    })


# ==========================================
# GET ALL TEMPLES
# ==========================================

@app.route("/api/temples", methods=["GET"])
@login_required
def get_temples():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM temples ORDER BY id
    """)

    temples = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return jsonify(temples)


# ==========================================
# SEARCH TEMPLES API
# ==========================================

@app.route("/api/search", methods=["GET"])
@login_required
def search_temples():

    query = request.args.get("q", "").strip()

    conn = get_db()
    cursor = conn.cursor()

    search_value = "%" + query + "%"

    cursor.execute("""
        SELECT * FROM temples
        WHERE name LIKE ?
        OR location LIKE ?
        OR deity LIKE ?
        ORDER BY id
    """, (search_value, search_value, search_value))

    results = [
        dict(row)
        for row in cursor.fetchall()
    ]

    conn.close()

    return jsonify(results)


# ==========================================
# GET ONE TEMPLE DETAILS
# ==========================================

@app.route("/api/temple/<int:temple_id>", methods=["GET"])
@login_required
def get_temple(temple_id):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM temples WHERE id = ?
    """, (temple_id,))

    temple = cursor.fetchone()

    conn.close()

    if temple is None:

        return jsonify({
            "error": "Temple not found"
        }), 404

    return jsonify(dict(temple))


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    initialize_db()

    print("Tulu Heritage database initialized.")
    print("Open http://127.0.0.1:5000/")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
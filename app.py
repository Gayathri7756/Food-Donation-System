from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import webbrowser
import threading

app = Flask(__name__)
DB_FILE = "food_donate.db"

# --- Setup Database ---
def setup_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        role TEXT CHECK(role IN ('donor','ngo','admin')) NOT NULL
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS donations (
        donation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        food_item TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        expiry_date TEXT,
        status TEXT DEFAULT 'available',
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        request_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        food_item TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        urgency TEXT CHECK(urgency IN ('low','medium','high')) DEFAULT 'low',
        status TEXT DEFAULT 'open',
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
        donation_id INTEGER,
        request_id INTEGER,
        match_date TEXT,
        FOREIGN KEY(donation_id) REFERENCES donations(donation_id),
        FOREIGN KEY(request_id) REFERENCES requests(request_id)
    )""")
    
    conn.commit()
    conn.close()

setup_db()

# --- Open browser automatically ---
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

threading.Timer(1, open_browser).start()

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

# Add User
@app.route('/add_user', methods=['GET','POST'])
@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        role = request.form["role"]

        conn = sqlite3.connect("food_donate.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, email, phone, role) VALUES (?, ?, ?, ?)",
                (name, email, phone, role)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "❌ Email already exists. Please use a different email."
        
        conn.close()
        return redirect(url_for("index"))

    return render_template("add_user.html")


# Add Donation
@app.route('/add_donation', methods=['GET','POST'])
def add_donation():
    if request.method == 'POST':
        user_id = request.form['user_id']
        food_item = request.form['food_item']
        quantity = request.form['quantity']
        expiry_date = request.form['expiry_date']
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO donations (user_id, food_item, quantity, expiry_date) VALUES (?,?,?,?)",
                       (user_id, food_item, quantity, expiry_date))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_donation.html')

# Add Request
@app.route('/add_request', methods=['GET','POST'])
def add_request():
    if request.method == 'POST':
        user_id = request.form['user_id']
        food_item = request.form['food_item']
        quantity = request.form['quantity']
        urgency = request.form['urgency']
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO requests (user_id, food_item, quantity, urgency) VALUES (?,?,?,?)",
                       (user_id, food_item, quantity, urgency))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('add_request.html')

# Match Donations
@app.route('/match')
def match():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("UPDATE donations SET status='expired' WHERE expiry_date < ? AND status='available'", (today,))
    
    cursor.execute("""
        SELECT d.donation_id, r.request_id, d.food_item, d.quantity, r.quantity
        FROM donations d JOIN requests r
        ON d.food_item = r.food_item
        WHERE d.status='available' AND r.status='open'
    """)
    matches = cursor.fetchall()
    match_messages = []
    for donation_id, request_id, food_item, d_qty, r_qty in matches:
        matched_qty = min(d_qty, r_qty)
        cursor.execute("INSERT INTO matches (donation_id, request_id, match_date) VALUES (?,?,?)",
                       (donation_id, request_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        new_d_qty = d_qty - matched_qty
        new_r_qty = r_qty - matched_qty
        if new_d_qty == 0:
            cursor.execute("UPDATE donations SET status='fulfilled' WHERE donation_id=?", (donation_id,))
        else:
            cursor.execute("UPDATE donations SET quantity=? WHERE donation_id=?", (new_d_qty, donation_id))
        if new_r_qty == 0:
            cursor.execute("UPDATE requests SET status='fulfilled' WHERE request_id=?", (request_id,))
        else:
            cursor.execute("UPDATE requests SET quantity=? WHERE request_id=?", (new_r_qty, request_id))
        match_messages.append(f"Matched {matched_qty} of {food_item} (Donation {donation_id} → Request {request_id})")
    conn.commit()
    conn.close()
    return render_template('match.html', messages=match_messages)

# Reports
@app.route('/reports')
def reports():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.name, COUNT(d.donation_id) as total_donations
        FROM users u JOIN donations d ON u.user_id=d.user_id
        GROUP BY u.name ORDER BY total_donations DESC LIMIT 5
    """)
    top_donors = cursor.fetchall()
    
    cursor.execute("""
        SELECT food_item, COUNT(*) as total_requests
        FROM requests GROUP BY food_item ORDER BY total_requests DESC LIMIT 5
    """)
    top_food = cursor.fetchall()
    conn.close()
    return render_template('reports.html', top_donors=top_donors, top_food=top_food)

# --- Start Flask app ---
if __name__ == "__main__":
    app.run(debug=True)


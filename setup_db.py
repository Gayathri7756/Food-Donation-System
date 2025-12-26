import sqlite3

# Connect to SQLite
conn = sqlite3.connect("food_donate.db")
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    role TEXT CHECK(role IN ('donor','ngo','admin')) NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS donations (
    donation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    food_item TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    expiry_date TEXT,
    status TEXT DEFAULT 'available',
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    food_item TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    urgency TEXT CHECK(urgency IN ('low','medium','high')) DEFAULT 'low',
    status TEXT DEFAULT 'open',
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    donation_id INTEGER,
    request_id INTEGER,
    match_date TEXT,
    FOREIGN KEY(donation_id) REFERENCES donations(donation_id),
    FOREIGN KEY(request_id) REFERENCES requests(request_id)
)
""")

print("Database setup complete ✅")
conn.commit()
conn.close()

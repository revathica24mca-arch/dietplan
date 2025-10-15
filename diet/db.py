# db.py
import sqlite3
from datetime import datetime
import json
from pathlib import Path

DB_PATH = Path("database.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS user_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    gender TEXT,
    weight REAL,
    height REAL,
    sleep REAL,
    activity TEXT,
    stress TEXT,
    work_type TEXT,

    bp TEXT,
    sugar TEXT,
    thyroid TEXT,
    pcod TEXT,
    cholesterol TEXT,
    heart TEXT,
    kidney TEXT,
    pregnancy TEXT,

    diet_pref TEXT,
    allergies TEXT,
    goal TEXT,

    bmi REAL,
    age_band TEXT,
    weight_class TEXT,

    profile_signature TEXT,   -- used to quickly find similar profiles
    diet_plan TEXT,           -- JSON string
    exercise_plan TEXT,       -- JSON string

    created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_profile_signature ON user_cases(profile_signature);
"""

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as con:
        con.executescript(SCHEMA)

def save_case(profile: dict, plan: dict):
    """
    Saves a generated plan along with the user's profile.
    plan = {"diet_plan": {...}, "exercise_plan": [...]}
    """
    with get_conn() as con:
        con.execute(
            """INSERT INTO user_cases (
                name, age, gender, weight, height, sleep, activity, stress, work_type,
                bp, sugar, thyroid, pcod, cholesterol, heart, kidney, pregnancy,
                diet_pref, allergies, goal,
                bmi, age_band, weight_class, profile_signature, diet_plan, exercise_plan, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                profile.get("name"),
                profile.get("age"),
                profile.get("gender"),
                profile.get("weight"),
                profile.get("height"),
                profile.get("sleep"),
                profile.get("activity"),
                profile.get("stress"),
                profile.get("work_type"),

                profile.get("bp"),
                profile.get("sugar"),
                profile.get("thyroid"),
                profile.get("pcod"),
                profile.get("cholesterol"),
                profile.get("heart"),
                profile.get("kidney"),
                profile.get("pregnancy"),

                profile.get("diet_pref"),
                profile.get("allergies"),
                profile.get("goal"),

                profile.get("bmi"),
                profile.get("age_band"),
                profile.get("weight_class"),
                profile.get("profile_signature"),
                json.dumps(plan.get("diet_plan")),
                json.dumps(plan.get("exercise_plan")),
                datetime.utcnow().isoformat()
            )
        )
        con.commit()

def find_by_signature(signature: str):
    with get_conn() as con:
        cur = con.execute(
            "SELECT diet_plan, exercise_plan FROM user_cases WHERE profile_signature = ? ORDER BY id DESC LIMIT 1",
            (signature,)
        )
        row = cur.fetchone()
        if not row:
            return None
        diet_json, ex_json = row
        return {
            "diet_plan": json.loads(diet_json),
            "exercise_plan": json.loads(ex_json)
        }

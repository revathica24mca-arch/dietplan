# app.py
from flask import Flask, render_template, request, redirect, url_for, session, send_file, make_response
import sqlite3
from datetime import datetime
import json
from pathlib import Path
from io import BytesIO

# Try to import HTML-to-PDF libraries
WEASYPRINT_AVAILABLE = False
XHTML2PDF_AVAILABLE = False
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    try:
        from xhtml2pdf import pisa
        XHTML2PDF_AVAILABLE = True
    except Exception:
        WEASYPRINT_AVAILABLE = False
        XHTML2PDF_AVAILABLE = False

# reportlab fallback
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# your diet generator - must return (plan_dict, profile_dict)
from diet_generator import generate_plan

app = Flask(__name__)
app.secret_key = "secret123"

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
    plan TEXT,
    plan_source TEXT,
    created_at TEXT
)
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(SCHEMA)
    conn.commit()
    conn.close()

init_db()

# ----------------- ROUTES -------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    # Basic fields
    name = request.form.get("name", "").strip()
    age = int(request.form.get("age") or 0)
    gender = request.form.get("gender", "")
    weight = float(request.form.get("weight") or 0)
    height = float(request.form.get("height") or 0)
    sleep = float(request.form.get("sleep") or 0)
    activity = request.form.get("activity", "low")
    stress = request.form.get("stress", "low")
    work_type = request.form.get("work_type", "")

    # Goals & prefs (optional in your form)
    goal = request.form.get("goal", "fitness").lower()
    diet_pref = (request.form.get("diet_pref") or "both").lower()
    allergies = (request.form.get("allergies") or "").strip()

    # Conditions coming from your form
    bp = request.form.get("bp", "normal").lower()
    sugar = request.form.get("sugar", "none").lower()
    thyroid = request.form.get("thyroid", "none").lower()
    pcod = request.form.get("pcod", "no").lower()
    cholesterol = request.form.get("cholesterol", "normal").lower()
    heart = request.form.get("heart", "no").lower()
    kidney = request.form.get("kidney", "no").lower()
    pregnancy = request.form.get("pregnancy", "na").lower()

    # Build a profile dict
    profile = {
        "name": name,
        "age": age,
        "gender": gender,
        "weight": weight,
        "height": height,
        "sleep": sleep,
        "activity": activity,
        "stress": stress,
        "work_type": work_type,
        "goal": goal,
        "diet_pref": diet_pref,
        "allergies": [a.strip().lower() for a in allergies.split(",") if a.strip()],
        "bp": bp,
        "sugar": sugar,
        "thyroid": thyroid,
        "pcod": pcod,
        "cholesterol": cholesterol,
        "heart": heart,
        "kidney": kidney,
        "pregnancy": pregnancy,
    }

    # Generate the plan (returns dicts)
    plan, profile = generate_plan(profile)

    # ---- Save into DB ----
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO user_cases
        (name, age, gender, weight, height, sleep, activity, stress, work_type,
         bp, sugar, thyroid, plan, plan_source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            name, age, gender, weight, height, sleep, activity, stress, work_type,
            bp, sugar, thyroid, json.dumps(plan), "Auto-generated", datetime.now().isoformat()
        ),
    )
    conn.commit()
    conn.close()

    # Save in session
    session["latest_profile"] = profile
    session["latest_plan"] = plan
    session["plan_source"] = "Auto-generated"

    return redirect(url_for("result"))

@app.route("/result")
def result():
    profile = session.get("latest_profile")
    plan = session.get("latest_plan")
    plan_source = session.get("plan_source")
    if not plan or not profile:
        return redirect(url_for("index"))
    return render_template("result.html", plan=plan, profile=profile, plan_source=plan_source)

# -------- PDF HELPERS ----------
def pdf_from_html_weasy(rendered_html: str) -> bytes:
    return HTML(string=rendered_html).write_pdf()

def pdf_from_html_xhtml2pdf(rendered_html: str) -> bytes:
    result = BytesIO()
    pisa_status = pisa.CreatePDF(rendered_html, dest=result)
    if pisa_status.err:
        raise RuntimeError("xhtml2pdf failed")
    return result.getvalue()

def pdf_from_reportlab(profile, plan) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(140, 760, "Personalized Diet & Fitness Plan")
    c.setFont("Helvetica", 11)
    y = 740

    def line(txt, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold", 12 if bold else 11)
        max_len = 95
        while txt:
            part = txt[:max_len]
            c.drawString(50, y, part)
            y -= 16
            txt = txt[max_len:]
            if y < 60:
                c.showPage()
                y = 760

    # Profile
    line(f"Name: {profile.get('name')}", bold=True)
    line(f"Age: {profile.get('age')}   Gender: {profile.get('gender')}")
    line(f"Height: {profile.get('height')} cm   Weight: {profile.get('weight')} kg")
    line(f"Goal: {profile.get('goal')}   Activity: {profile.get('activity')}")
    y -= 6

    # Diet Plan
    line("Diet Plan:", bold=True)
    for day, meals in (plan.get("diet_plan") or {}).items():
        line(f"{day}: B={meals.get('Breakfast')} | L={meals.get('Lunch')} | D={meals.get('Dinner')}")
    y -= 6

    # Exercise Plan
    line("Exercise Plan:", bold=True)
    for ex in (plan.get("exercise_plan") or []):
        line(f"- {ex}")
    y -= 6

    # Notes
    notes = plan.get("notes") or []
    if notes:
        line("Recommendations:", bold=True)
        for n in notes:
            line(f"- {n}")

    c.save()
    buf.seek(0)
    return buf.read()

@app.route("/download_pdf")
def download_pdf():
    profile = session.get("latest_profile")
    plan = session.get("latest_plan")
    plan_source = session.get("plan_source")
    if not plan or not profile:
        return redirect(url_for("index"))

    rendered_html = render_template("result.html", plan=plan, profile=profile, plan_source=plan_source)

    try:
        if WEASYPRINT_AVAILABLE:
            pdf_bytes = pdf_from_html_weasy(rendered_html)
        elif XHTML2PDF_AVAILABLE:
            pdf_bytes = pdf_from_html_xhtml2pdf(rendered_html)
        else:
            pdf_bytes = pdf_from_reportlab(profile, plan)

        return send_file(BytesIO(pdf_bytes), as_attachment=True,
                         download_name="diet_plan.pdf", mimetype="application/pdf")

    except Exception:
        pdf_bytes = pdf_from_reportlab(profile, plan)
        return send_file(BytesIO(pdf_bytes), as_attachment=True,
                         download_name="diet_plan.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)

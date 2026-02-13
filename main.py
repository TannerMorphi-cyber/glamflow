from fastapi import FastAPI, Body
from datetime import datetime
import sqlite3

app = FastAPI()

conn = sqlite3.connect("appointments.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    service TEXT,
    date TEXT,
    time TEXT,
    code TEXT,
    status TEXT
)
""")
conn.commit()

@app.post("/create-appointment")
def create_appointment(data: dict = Body(...)):
    cursor.execute("""
        INSERT INTO appointments (name, service, date, time, code, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get("name"),
        data.get("service"),
        data.get("date"),
        data.get("time"),
        data.get("code"),
        data.get("status"),
    ))
    conn.commit()

    return {"status": "ok"}

@app.get("/today-appointments")
def today_appointments():
    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT name, service, date, time, code, status
        FROM appointments
        WHERE date = ?
    """, (today,))

    rows = cursor.fetchall()

    return [
        {
            "name": r[0],
            "service": r[1],
            "date": r[2],
            "time": r[3],
            "code": r[4],
            "status": r[5]
        }
        for r in rows
    ]

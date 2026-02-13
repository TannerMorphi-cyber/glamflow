from fastapi import FastAPI, Body
from datetime import datetime
import psycopg2
import os

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

conn = None
cursor = None

def get_connection():
    global conn, cursor
    if conn is None:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            name TEXT,
            service TEXT,
            date TEXT,
            time TEXT,
            code TEXT,
            status TEXT
        )
        """)
        conn.commit()
    return conn, cursor


@app.post("/create-appointment")
def create_appointment(data: dict = Body(...)):
    conn, cursor = get_connection()

    cursor.execute("""
        INSERT INTO appointments (name, service, date, time, code, status)
        VALUES (%s, %s, %s, %s, %s, %s)
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
    conn, cursor = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT name, service, date, time, code, status
        FROM appointments
        WHERE date = %s
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

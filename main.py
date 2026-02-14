import os
import psycopg2
from fastapi import FastAPI, Body
from datetime import datetime

app = FastAPI()

# ✅ Primero definimos la variable
DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


@app.post("/create-appointment")
def create_appointment(data: dict = Body(...)):
    conn = get_connection()
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
    cursor.close()
    conn.close()

    return {"status": "ok"}


from datetime import date

@app.get("/today-appointments/{business_id}")
def get_today_appointments(business_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today()

    cursor.execute("""
        SELECT name, service, date, time, code, status
        FROM appointments
        WHERE date = %s
        AND business_id = %s
    """, (today, business_id))

    appointments = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"appointments": appointments}


    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT name, service, date, time, code, status
        FROM appointments
        WHERE date = %s
    """, (today,))

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

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
def create_business_fk():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN IF NOT EXISTS business_id INTEGER;
        """)

        cursor.execute("""
            ALTER TABLE appointments
            ADD CONSTRAINT fk_business
            FOREIGN KEY (business_id)
            REFERENCES businesses(id)
            ON DELETE CASCADE;
        """)

        conn.commit()
    except Exception as e:
        print("FK ya existe o error:", e)
    finally:
        cursor.close()
        conn.close()
@app.on_event("startup")
def startup_event():
    create_business_fk()
def fix_old_appointments():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET business_id = 1
        WHERE business_id IS NULL;
    """)

    conn.commit()
    cursor.close()
    conn.close()
@app.on_event("startup")
def startup_event():
    create_business_fk()
    fix_old_appointments()

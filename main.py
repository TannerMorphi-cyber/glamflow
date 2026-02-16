from fastapi import FastAPI, HTTPException
from datetime import datetime, date
import pytz
import psycopg2
import os
import secrets

app = FastAPI()

# =====================================
# 🔹 ZONA HORARIA MÉXICO
# =====================================
def get_mexico_today():
    mexico_tz = pytz.timezone("America/Mexico_City")
    mexico_now = datetime.now(mexico_tz)
    return mexico_now.date()


# =====================================
# 🔹 CONEXIÓN DATABASE
# =====================================
def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


# =====================================
# 🔹 MIGRACIONES AUTOMÁTICAS
# =====================================
def run_migrations():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            ALTER TABLE businesses
            ADD COLUMN IF NOT EXISTS api_key TEXT;
        """)

        cursor.execute("""
            ALTER TABLE businesses
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
        """)

        cursor.execute("""
            ALTER TABLE businesses
            ADD COLUMN IF NOT EXISTS plan_expires DATE;
        """)

        cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN IF NOT EXISTS business_id INTEGER;
        """)

        cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_business'
            ) THEN
                ALTER TABLE appointments
                ADD CONSTRAINT fk_business
                FOREIGN KEY (business_id)
                REFERENCES businesses(id)
                ON DELETE CASCADE;
            END IF;
        END$$;
        """)

        conn.commit()
    finally:
        cursor.close()
        conn.close()


@app.on_event("startup")
def startup_event():
    run_migrations()


# =====================================
# 🔹 VALIDAR NEGOCIO + PLAN
# =====================================
def validate_business(api_key: str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, is_active, plan_expires
            FROM businesses
            WHERE TRIM(api_key) = %s;
        """, (api_key.strip(),))

        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="API key inválida")

        business_id, is_active, plan_expires = result

        if not is_active:
            raise HTTPException(status_code=403, detail="Suscripción inactiva")

        today = get_mexico_today()

        if plan_expires and plan_expires < today:
            raise HTTPException(status_code=403, detail="Plan expirado")

        return business_id

    finally:
        cursor.close()
        conn.close()


# =====================================
# 🔹 CREAR NEGOCIO
# =====================================
@app.post("/create-business")
def create_business(data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    api_key = "sk_" + secrets.token_hex(16)

    try:
        cursor.execute("""
            INSERT INTO businesses (name, api_key, is_active, plan_expires)
            VALUES (%s, %s, TRUE, %s)
            RETURNING id;
        """, (
            data.get("name"),
            api_key,
            get_mexico_today()
        ))

        business_id = cursor.fetchone()[0]
        conn.commit()

        return {
            "business_id": business_id,
            "api_key": api_key
        }

    finally:
        cursor.close()
        conn.close()


# =====================================
# 🔹 CREAR CITA (USADO POR EL ASISTENTE)
# =====================================
@app.post("/appointments")
def create_appointment(data: dict):
    api_key = data.get("api_key")

    if not api_key:
        raise HTTPException(status_code=400, detail="Falta API key")

    business_id = validate_business(api_key)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Validar que no exista cita duplicada
        cursor.execute("""
            SELECT id FROM appointments
            WHERE business_id = %s
            AND date = %s
            AND time = %s;
        """, (
            business_id,
            data.get("date"),
            data.get("time")
        ))

        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Horario no disponible")

        code = "CITA-" + secrets.token_hex(3)

        cursor.execute("""
            INSERT INTO appointments
            (business_id, name, service, date, time, code, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            business_id,
            data.get("name"),
            data.get("service"),
            data.get("date"),
            data.get("time"),
            code,
            "confirmada"
        ))

        conn.commit()

        return {
            "message": "Cita creada correctamente",
            "code": code
        }

    finally:
        cursor.close()
        conn.close()


# =====================================
# 🔹 OBTENER CITAS DEL DÍA
# =====================================
@app.get("/today-appointments")
def get_today_appointments(api_key: str):

    business_id = validate_business(api_key)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        today = get_mexico_today().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT name, service, date, time, code, status
            FROM appointments
            WHERE date = %s
            AND business_id = %s;
        """, (today, business_id))

        rows = cursor.fetchall()

        appointments = []
        for row in rows:
            appointments.append({
                "name": row[0],
                "service": row[1],
                "date": row[2],
                "time": row[3],
                "code": row[4],
                "status": row[5],
            })

        return {"appointments": appointments}

    finally:
        cursor.close()
        conn.close()

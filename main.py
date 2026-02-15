def get_mexico_today():
    mexico_tz = pytz.timezone("America/Mexico_City")
    mexico_now = datetime.now(mexico_tz)
    return mexico_now.date()

from fastapi import FastAPI, HTTPException
from datetime import datetime
import pytz
import psycopg2
import os
import secrets

app = FastAPI()


# ===============================
# 🔹 CONEXIÓN DATABASE
# ===============================
def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


# ===============================
# 🔹 CREAR COLUMNAS NECESARIAS
# ===============================
def run_migrations():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Agregar business_id a appointments
        cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN IF NOT EXISTS business_id INTEGER;
        """)

        # Agregar api_key a businesses
        cursor.execute("""
            ALTER TABLE businesses
            ADD COLUMN IF NOT EXISTS api_key TEXT;
        """)

        # Crear FK si no existe
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

    except Exception as e:
        print("Migration error:", e)

    finally:
        cursor.close()
        conn.close()


# ===============================
# 🔹 REPARAR CITAS VIEJAS
# ===============================
def fix_old_appointments():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE appointments
            SET business_id = 1
            WHERE business_id IS NULL;
        """)
        conn.commit()
    except:
        pass
    finally:
        cursor.close()
        conn.close()


@app.on_event("startup")
def startup_event():
    run_migrations()
    fix_old_appointments()


# ===============================
# 🔹 CREAR NEGOCIO (AUTO API KEY)
# ===============================
@app.post("/create-business")
def create_business(data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    api_key = "sk_" + secrets.token_hex(16)

    try:
        cursor.execute("""
            INSERT INTO businesses (name, api_key)
            VALUES (%s, %s)
            RETURNING id;
        """, (data.get("name"), api_key))

        business_id = cursor.fetchone()[0]
        conn.commit()

        return {
            "business_id": business_id,
            "api_key": api_key
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


# ===============================
# 🔹 CREAR CITA
# ===============================
@app.post("/appointments")
def create_appointment(data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO appointments 
            (business_id, name, service, date, time, code, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get("business_id"),
            data.get("name"),
            data.get("service"),
            data.get("date"),
            data.get("time"),
            data.get("code"),
            data.get("status"),
        ))

        conn.commit()
        return {"message": "Cita creada correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


# ===============================
# 🔹 CONSULTAR CITAS DE HOY POR API KEY
# ===============================
@app.get("/today-appointments")
def get_today_appointments(api_key: str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        today = get_mexico_today().strftime("%Y-%m-%d")

        # Buscar negocio
        cursor.execute("""
            SELECT id FROM businesses
            WHERE api_key = %s;
        """, (api_key,))

        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="API key inválida")

        business_id = result[0]

        # Obtener citas del día
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

from fastapi import FastAPI
from datetime import date
import psycopg2
import os

app = FastAPI()

# 🔹 Conexión a Railway PostgreSQL
def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])


# 🔹 Crear columna y FK si no existen
def create_business_fk():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            ALTER TABLE appointments
            ADD COLUMN IF NOT EXISTS business_id INTEGER;
        """)

        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
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
        print("Error FK:", e)
    finally:
        cursor.close()
        conn.close()


# 🔹 Reparar citas viejas
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
    except Exception as e:
        print("Error fix:", e)
    finally:
        cursor.close()
        conn.close()


@app.on_event("startup")
def startup_event():
    create_business_fk()
    fix_old_appointments()


# 🔹 Crear cita
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
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()


# 🔹 Obtener citas de hoy por negocio
@app.get("/today-appointments/{business_id}")
def get_today_appointments(business_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        today = date.today().strftime("%Y-%m-%d")

        cursor.execute("""
            SELECT name, service, date, time, code, status
            FROM appointments
            WHERE date = %s
            AND business_id = %s
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
        return {"error": str(e)}

    finally:
        cursor.close()
        conn.close()

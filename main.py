@app.get("/today-appointments")
def get_today_appointments(api_key: str):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        today = get_mexico_today()

        # 🔎 Buscar negocio y validar plan
        cursor.execute("""
            SELECT id, is_active, plan_expires
            FROM businesses
            WHERE api_key = %s;
        """, (api_key,))

        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="API key inválida")

        business_id, is_active, plan_expires = result

        # 🚫 Negocio inactivo
        if not is_active:
            raise HTTPException(status_code=403, detail="Suscripción inactiva")

        # 🚫 Plan expirado
        if plan_expires and plan_expires < today:
            raise HTTPException(status_code=403, detail="Plan expirado")

        # 📅 Obtener citas del día
        cursor.execute("""
            SELECT name, service, date, time, code, status
            FROM appointments
            WHERE date = %s
            AND business_id = %s;
        """, (today.strftime("%Y-%m-%d"), business_id))

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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

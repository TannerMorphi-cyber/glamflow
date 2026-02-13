from fastapi import FastAPI, Body
from datetime import datetime

app = FastAPI()

appointments = []

@app.get("/")
def root():
    return {"status": "GLAMFLOW activo 🚀"}

@app.post("/create-appointment")
def create_appointment(data: dict = Body(...)):
    appointments.append(data)
    return {
        "status": "ok",
        "guardado": data,
        "total_en_memoria": len(appointments)
    }

@app.get("/today-appointments")
def today_appointments():
    return {
        "total_en_memoria": len(appointments),
        "contenido": appointments
    }

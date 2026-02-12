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
    return {"status": "ok"}

@app.get("/today-appointments")
def today_appointments():
    today = datetime.now().strftime("%Y-%m-%d")
    return [
        a for a in appointments
        if a.get("date") == today
    ]

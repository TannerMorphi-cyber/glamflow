from fastapi import FastAPI, Request
from fastapi.responses import Response

app = FastAPI(title="GLAMFLOW")

@app.get("/")
def home():
    return {
        "status": "GLAMFLOW backend activo 🚀",
        "message": "Todo listo para conectar WhatsApp"
    }

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>
Hola 👋 Bienvenida a Salón BELLA FLOW ✨
Soy GLAMFLOW, el asistente automático de citas.

Responde con un número 👇

1️⃣ Agendar cita
2️⃣ Ver precios
3️⃣ Ubicación
4️⃣ Hablar con el salón
    </Message>
</Response>
"""
    return Response(content=twiml, media_type="application/xml")

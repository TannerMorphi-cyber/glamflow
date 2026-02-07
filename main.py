from fastapi import FastAPI, Request
from fastapi.responses import Response

app = FastAPI(title="GLAMFLOW")

# Estados en memoria (MVP)
sessions = {}

@app.get("/")
def home():
    return {"status": "GLAMFLOW activo 🚀"}

def menu_principal():
    return (
        "Hola 👋 Bienvenida a Salón BELLA FLOW ✨\n"
        "Soy GLAMFLOW, el asistente automático de citas.\n\n"
        "Responde con un número 👇\n\n"
        "1️⃣ Agendar cita\n"
        "2️⃣ Ver precios\n"
        "3️⃣ Ubicación\n"
        "4️⃣ Hablar con el salón"
    )

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    user_msg = form.get("Body", "").strip()
    phone = form.get("From", "")

    # Estado actual del usuario
    state = sessions.get(phone, "menu")

    # Lógica de conversación
    if state == "menu":
        if user_msg == "1":
            sessions[phone] = "servicio"
            reply = (
                "Perfecto 💖\n"
                "¿Qué servicio deseas agendar?\n\n"
                "1️⃣ Corte\n"
                "2️⃣ Uñas\n"
                "3️⃣ Tinte\n"
                "4️⃣ Tratamiento"
            )
        elif user_msg == "2":
            reply = (
                "💲 Lista de precios\n\n"
                "✂️ Corte: $200\n"
                "💅 Uñas: $350\n"
                "🎨 Tinte: $600\n"
                "💆 Tratamiento: $450\n\n"
                "Responde 1️⃣ para agendar cita"
            )
        elif user_msg == "3":
            reply = (
                "📍 Estamos ubicados en:\n"
                "Av. Principal #123\n\n"
                "https://maps.google.com"
            )
        elif user_msg == "4":
            reply = "Perfecto 💬 En un momento te comunicamos con el salón."
        else:
            reply = menu_principal()

    elif state == "servicio":
        servicios = {
            "1": "Corte",
            "2": "Uñas",
            "3": "Tinte",
            "4": "Tratamiento"
        }
        if user_msg in servicios:
            sessions[phone] = "menu"
            reply = f"✨ Servicio *{servicios[user_msg]}* seleccionado.\n\n(Agenda completa viene en el siguiente paso 😉)"
        else:
            reply = "Por favor responde con un número del 1 al 4."

    else:
        sessions[phone] = "menu"
        reply = menu_principal()

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply}</Message>
</Response>
"""
    return Response(content=twiml, media_type="application/xml")

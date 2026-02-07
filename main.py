from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI(title="GLAMFLOW")

@app.get("/")
def home():
    return {
        "status": "GLAMFLOW backend activo 🚀",
        "message": "Todo listo para conectar WhatsApp"
    }

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook para WhatsApp (Twilio)
    """
    form = await request.form()
    incoming_msg = form.get("Body", "").strip().lower()

    # Respuesta básica (por ahora)
    response_message = (
        "Hola 👋 Bienvenida a Salón BELLA FLOW ✨\n"
        "Soy GLAMFLOW, el asistente automático de citas.\n\n"
        "Responde con un número 👇\n\n"
        "1️⃣ Agendar cita\n"
        "2️⃣ Ver precios\n"
        "3️⃣ Ubicación\n"
        "4️⃣ Hablar con el salón"
    )

    twilio_response = f"""
<Response>
    <Message>{response_message}</Message>
</Response>
""".strip()

    return PlainTextResponse(content=twilio_response, media_type="application/xml")

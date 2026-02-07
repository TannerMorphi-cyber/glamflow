from fastapi import FastAPI

app = FastAPI(title="GLAMFLOW")

@app.get("/")
def home():
    return {
        "status": "GLAMFLOW backend activo 🚀",
        "message": "Todo listo para conectar WhatsApp"
    }

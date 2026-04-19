from fastapi import FastAPI
import socket

app = FastAPI()

@app.get("/")
def home():
    return {
        "message": "Hello from FastAPI CI/CD 🚀",
        "hostname": socket.gethostname()
    }

@app.get("/health")
def health():
    return {"status": "UP"}

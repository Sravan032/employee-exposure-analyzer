from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "message": "FastAPI is working on Vercel"
    }
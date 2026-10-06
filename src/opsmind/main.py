from fastapi import FastAPI

app = FastAPI(title="Opsmind")


@app.get("/health")
def health():
    return {"status": "ok"}

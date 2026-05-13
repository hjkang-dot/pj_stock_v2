from fastapi import FastAPI

app = FastAPI(title="PJ Stock Backend")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

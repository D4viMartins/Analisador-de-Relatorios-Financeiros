from fastapi import FastAPI

from app.routes.ask import router as ask_router
from app.routes.upload import router as upload_router

app = FastAPI(
    title="Analisador de Relatórios Financeiros",
    version="0.2.0",
)

app.include_router(upload_router)
app.include_router(ask_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

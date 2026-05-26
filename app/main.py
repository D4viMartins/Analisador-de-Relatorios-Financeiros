from fastapi import FastAPI

from app.routes.upload import router as upload_router

app = FastAPI(
    title="Analisador de Relatórios Financeiros",
    version="0.1.0",
)

app.include_router(upload_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

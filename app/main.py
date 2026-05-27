from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.session import init_db
from app.routes.analyze import router as analyze_router
from app.routes.ask import router as ask_router
from app.routes.compare import router as compare_router
from app.routes.upload import router as upload_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Analisador de Relatórios Financeiros",
    version="0.4.0",
    lifespan=lifespan,
)

app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(analyze_router)
app.include_router(compare_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.db.session import init_db
from app.dependencies.auth import require_api_key
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
    version="0.5.0",
    lifespan=lifespan,
)

protected = [Depends(require_api_key)]
app.include_router(upload_router, dependencies=protected)
app.include_router(ask_router, dependencies=protected)
app.include_router(analyze_router, dependencies=protected)
app.include_router(compare_router, dependencies=protected)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

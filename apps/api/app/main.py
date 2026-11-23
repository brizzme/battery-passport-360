from typing import Annotated, Literal

import psycopg
from fastapi import Depends, FastAPI, Response
from pydantic import BaseModel

from .summary import router as summary_router
from .copilot import router as copilot_router
from .research import router as research_router
from .db import connect
from .fleet import router as fleet_router
from .fleet_health import router as fleet_health_router


class Health(BaseModel):
    status: Literal["ok", "unavailable"]
    database: Literal["ready", "unavailable"]


def database_ready() -> bool:
    try:
        with connect() as conn:
            return conn.execute(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            ).fetchone() is not None
    except psycopg.Error:
        return False


app = FastAPI(title="Battery Passport 360", version="0.1.0")


app.include_router(fleet_router)
app.include_router(fleet_health_router)
app.include_router(research_router)
app.include_router(copilot_router)
app.include_router(summary_router)


@app.get("/health", responses={503: {"model": Health}})
def health(response: Response, ready: Annotated[bool, Depends(database_ready)]) -> Health:
    if ready:
        return Health(status="ok", database="ready")
    response.status_code = 503
    return Health(status="unavailable", database="unavailable")

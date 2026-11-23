import logging
from typing import Annotated, Literal

import psycopg
from fastapi import Depends, FastAPI, Response
from pydantic import BaseModel

from .summary import router as summary_router
from .copilot import router as copilot_router
from .research import router as research_router
from .db import Settings, connect
from .fleet import router as fleet_router
from .fleet_health import router as fleet_health_router


class Health(BaseModel):
    status: Literal["ok", "unavailable"]
    database: Literal["ready", "unavailable"]


log = logging.getLogger("uvicorn.error")


def database_ready() -> bool:
    try:
        with connect() as conn:
            ready = conn.execute(
                "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
            ).fetchone() is not None
        if not ready:
            log.warning("health: connected to %s but the vector extension is missing (migrations not applied?)", Settings().pghost)
        return ready
    except psycopg.Error as exc:
        # Host and error class/message only; psycopg never includes the password.
        log.warning("health: database unavailable at host=%s: %s: %s", Settings().pghost, type(exc).__name__, str(exc).strip()[:300])
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

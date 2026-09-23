from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.core.database import init_db
from app.core.config import settings

app = FastAPI(
    title="Healthcare Triage Assistant",
    description=f"Stage 1 backend. \n\n**DISCLAIMER:** {settings.DISCLAIMER}",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {"status": "ok", "version": "1.0.0", "disclaimer": settings.DISCLAIMER}

app.include_router(api_router, prefix="/api/v1")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

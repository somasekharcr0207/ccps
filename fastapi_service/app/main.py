from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import payments

app = FastAPI(
    title="Credit Card Payment System - Payment Service",
    description="Simulated payment processing (PENDING -> SUCCESS/FAILED). Authenticate with the JWT "
                "access token obtained from the Django `/api/auth/login/` endpoint.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",")],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(payments.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

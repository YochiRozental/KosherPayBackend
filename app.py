from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.web_api import router as web_router
from routes.admin_api import router as admin_router
from routes.ivr_api import router as ivr_router


# -------------------------
# Logging
# -------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger("kosherpay")

# -------------------------
# App
# -------------------------
app = FastAPI(
    title="KosherPay API",
    description="Payment system API",
    version="1.0.0",
)

# -------------------------
# Exception handling
# -------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)

    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal Server Error"},
    )

# -------------------------
# CORS
# -------------------------
cors_env = (os.getenv("CORS_ORIGINS") or "").strip()

if cors_env:
    allow_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
else:
    allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Routes
# -------------------------
@app.get("/", include_in_schema=False)
async def health():
    return {"status": "ok", "service": "kosherpay-backend"}

app.include_router(web_router)
app.include_router(admin_router)
app.include_router(ivr_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
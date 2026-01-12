from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse
from fastapi import Request

from routes.web_api import router as web_router
from routes.admin_api import router as admin_router
from routes.ivr_api import router as ivr_router

app = FastAPI(
    title="KosherPay API",
    description="Payment system API",
    version="1.0.0"
)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal Server Error", "error": str(exc)},
    )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health():
    return {"status": "ok", "service": "kosherpay-backend"}

app.include_router(web_router)
app.include_router(admin_router)
app.include_router(ivr_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

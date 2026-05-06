from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.stats import router as stats_router
from app.api.v1.hotels import router as hotels_router
from app.api.v1.health import router as health_router
from app.api.webhooks.whatsapp import router as webhook_router
from app.api.webhooks.razorpay import router as razorpay_router
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-tenant WhatsApp Hotel Booking SaaS",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for templates or dashboard
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register Routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(stats_router, prefix=f"{settings.API_V1_STR}/stats", tags=["stats"])
app.include_router(hotels_router, prefix=f"{settings.API_V1_STR}/hotels", tags=["hotels"])
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(webhook_router, tags=["webhooks"])
app.include_router(razorpay_router, prefix="/webhooks", tags=["webhooks"])

@app.get("/")
async def root():
    from app.db.firebase import get_db
    db = get_db()
    return {
        "status": f"{settings.PROJECT_NAME} is running",
        "firebase_connected": db is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

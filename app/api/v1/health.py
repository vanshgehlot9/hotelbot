from fastapi import APIRouter, Depends
from app.api.dependencies import get_firestore_db, require_superadmin
from app.core.config import settings
import redis as redis_lib

router = APIRouter()

@router.get("/health")
async def health_check(
    db=Depends(get_firestore_db),
    current_user: dict = Depends(require_superadmin)
):
    """Returns real system health status."""
    status = {}

    # 1. Firebase Firestore
    try:
        db.collection("users").limit(1).stream()
        status["firebase"] = "Connected"
    except Exception as e:
        status["firebase"] = f"Error: {str(e)[:40]}"

    # 2. Redis
    try:
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        status["redis"] = "Running"
    except Exception:
        status["redis"] = "Unavailable"

    # 3. WhatsApp credentials
    if settings.ACCESS_TOKEN and settings.PHONE_NUMBER_ID:
        status["whatsapp"] = "Configured"
    else:
        status["whatsapp"] = "Not Configured"

    # 4. Gemini AI
    if settings.GEMINI_API_KEY:
        status["gemini"] = "Configured"
    else:
        status["gemini"] = "Not Configured"

    # 5. Razorpay
    if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_ID != "mock_key_id":
        status["razorpay"] = "Configured"
    else:
        status["razorpay"] = "Test Mode"

    return status

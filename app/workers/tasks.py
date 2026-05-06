import logging
import re
from app.workers.celery_app import celery_app
from app.services.whatsapp import whatsapp_service
from app.db.firebase import get_db

logger = logging.getLogger(__name__)

# ─── Firestore helpers ──────────────────────────────────────────────────────────

def get_user_state(phone: str) -> dict:
    db = get_db()
    if not db:
        return {}
    try:
        doc = db.collection("users_state").document(phone).get()
        return doc.to_dict() if doc.exists else {}
    except Exception as e:
        logger.error(f"get_user_state error: {e}")
        return {}

def update_user_state(phone: str, data: dict):
    db = get_db()
    if not db:
        return
    try:
        db.collection("users_state").document(phone).set(data, merge=True)
    except Exception as e:
        logger.error(f"update_user_state error: {e}")

def clear_user_state(phone: str):
    db = get_db()
    if not db:
        return
    try:
        db.collection("users_state").document(phone).delete()
    except Exception as e:
        logger.error(f"clear_user_state error: {e}")

# ─── Fast keyword extraction (no external API calls) ────────────────────────────

INDIAN_CITIES = [
    "jaipur", "jodhpur", "udaipur", "ajmer", "kota", "bikaner", "jaisalmer",
    "mumbai", "delhi", "new delhi", "bangalore", "hyderabad", "chennai",
    "kolkata", "pune", "ahmedabad", "surat", "goa", "agra", "varanasi",
    "lucknow", "chandigarh", "manali", "shimla", "mussoorie", "haridwar",
    "rishikesh", "amritsar", "gurgaon", "noida", "indore", "bhopal",
    "nagpur", "patna", "ranchi", "bhubaneswar", "visakhapatnam", "coimbatore",
    "mysore", "kochi", "thiruvananthapuram", "madurai", "srinagar", "leh"
]

GREETINGS = [
    "hi", "hii", "hiii", "hello", "helo", "hey", "heyy", "yo", "sup",
    "namaste", "namaskar", "menu", "restart", "reset", "start", "begin"
]

def extract_info(text: str, user_state: dict) -> dict:
    """Pure keyword extraction — instant, no API calls."""
    result = {}
    msg = text.lower().strip()

    # City detection
    for city in INDIAN_CITIES:
        if city in msg:
            result["city"] = city.title()
            break

    # Date detection YYYY-MM-DD
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)
    if len(dates) >= 2:
        result["checkin"] = dates[0]
        result["checkout"] = dates[1]
    elif len(dates) == 1:
        if user_state.get("checkin") and not user_state.get("checkout"):
            result["checkout"] = dates[0]
        else:
            result["checkin"] = dates[0]

    # Date detection DD/MM/YYYY or DD-MM-YYYY
    if not dates:
        alt_dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', text)
        if alt_dates:
            from datetime import datetime
            try:
                d = datetime.strptime(alt_dates[0].replace("/", "-"), "%d-%m-%Y")
                formatted = d.strftime("%Y-%m-%d")
                if user_state.get("checkin") and not user_state.get("checkout"):
                    result["checkout"] = formatted
                else:
                    result["checkin"] = formatted
            except Exception:
                pass

    # Room count
    m = re.search(r'(\d+)\s*room', msg)
    if m:
        result["rooms"] = int(m.group(1))

    # Email
    email_m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', msg)
    if email_m:
        result["guest_email"] = email_m.group(0)

    # Name (only if city + checkout known and no name yet)
    if (user_state.get("city") and user_state.get("checkout")
            and not user_state.get("guest_name")
            and not email_m and not dates and not m and "city" not in result):
        result["guest_name"] = text.strip().title()

    return result

# ─── Main Celery task ────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=2)
def process_whatsapp_message(self, phone: str, text: str):
    logger.info(f"Processing message from {phone}: {text}")
    try:
        user_state = get_user_state(phone)
        text_clean = text.strip()

        # 1. Greeting / reset
        if text_clean.lower() in GREETINGS:
            clear_user_state(phone)
            whatsapp_service.send_message(
                phone,
                "👋 Welcome to *HotelBot*!\n\n"
                "I help you book hotels across India.\n\n"
                "🏙️ *Which city would you like to stay in?*\n\n"
                "_(e.g. Jaipur, Mumbai, Goa, Delhi, Shimla...)_"
            )
            return

        # 2. Fast keyword extraction
        extracted = extract_info(text_clean, user_state)

        # Merge into state
        for key, val in extracted.items():
            if val and str(val) not in ("null", "None", ""):
                user_state[key] = val

        update_user_state(phone, user_state)

        # 3. Decision engine — ask for missing info
        if not user_state.get("city"):
            whatsapp_service.send_message(
                phone,
                "🏙️ Which *city* would you like to book a hotel in?\n\n"
                "_(e.g. Jaipur, Mumbai, Goa, Delhi, Shimla...)_"
            )
            return

        if not user_state.get("checkin"):
            whatsapp_service.send_message(
                phone,
                f"📅 *Check-in date* for *{user_state['city']}*?\n"
                "_(Format: YYYY-MM-DD, e.g. 2025-06-10)_"
            )
            return

        if not user_state.get("checkout"):
            whatsapp_service.send_message(
                phone,
                "📅 *Check-out date*?\n"
                "_(Format: YYYY-MM-DD, e.g. 2025-06-12)_"
            )
            return

        if not user_state.get("guest_name"):
            whatsapp_service.send_message(
                phone,
                "👤 Please share the *guest name* for the booking:"
            )
            return

        # 4. All info collected — show confirmation
        whatsapp_service.send_message(
            phone,
            f"✅ *Booking Summary*\n\n"
            f"🏙️ City: {user_state.get('city')}\n"
            f"📅 Check-in: {user_state.get('checkin')}\n"
            f"📅 Check-out: {user_state.get('checkout')}\n"
            f"👤 Guest: {user_state.get('guest_name')}\n\n"
            f"Type *confirm* to book or *reset* to start over."
        )

    except Exception as exc:
        logger.error(f"Error processing message from {phone}: {exc}")
        if self.request.retries >= self.max_retries - 1:
            try:
                whatsapp_service.send_message(
                    phone,
                    "😓 Something went wrong. Please type *hi* to start again."
                )
            except Exception:
                pass
        else:
            self.retry(exc=exc, countdown=3)

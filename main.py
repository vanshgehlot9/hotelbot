import os
import json
import logging
import time
import re
import uuid
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import google.generativeai as google_genai
from dotenv import load_dotenv
from datetime import datetime
from receipt_generator import generate_receipt

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ACCESS_TOKEN    = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN    = os.getenv("VERIFY_TOKEN", "12345")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")

# ── Gemini ────────────────────────────────────────────────────────────────────
if GEMINI_API_KEY:
    google_genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = google_genai.GenerativeModel("gemini-1.5-flash")
else:
    logger.warning("GEMINI_API_KEY not set.")
    gemini_model = None

# ── Firebase ──────────────────────────────────────────────────────────────────
try:
    if not firebase_admin._apps:
        cred_value = os.getenv("FIREBASE_CREDENTIALS")
        if cred_value:
            if cred_value.strip().startswith("{"):
                # Parse as JSON string
                cred_dict = json.loads(cred_value)
                firebase_admin.initialize_app(credentials.Certificate(cred_dict))
            elif os.path.exists(cred_value):
                # Parse as file path
                firebase_admin.initialize_app(credentials.Certificate(cred_value))
            else:
                logger.warning(f"Firebase creds not found or invalid format: {cred_value[:20]}...")
        else:
            logger.warning("FIREBASE_CREDENTIALS not set.")
    db = firestore.client() if firebase_admin._apps else None
except Exception as e:
    logger.error(f"Firebase init failed: {e}")
    db = None

app = FastAPI(title="Hotel Booking WhatsApp Bot")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── Seed Data (real hotels per city) ─────────────────────────────────────────
SEED_HOTELS = [
    # Delhi
    {"name": "The Leela Palace New Delhi", "city": "Delhi",     "price_per_night": 18000, "rating": 4.8, "amenities": "Pool, Spa, Free WiFi, Gym", "description": "5-star luxury on Diplomatic Enclave"},
    {"name": "ITC Maurya New Delhi",       "city": "Delhi",     "price_per_night": 14000, "rating": 4.7, "amenities": "Multiple Restaurants, Spa, WiFi", "description": "Iconic heritage hotel in Chanakyapuri"},
    {"name": "Bloom Hotel - Vasant Kunj",  "city": "Delhi",     "price_per_night": 3500,  "rating": 4.3, "amenities": "Free WiFi, AC, Breakfast", "description": "Modern boutique near Vasant Kunj Mall"},
    # Mumbai
    {"name": "Taj Mahal Palace Mumbai",    "city": "Mumbai",    "price_per_night": 22000, "rating": 4.9, "amenities": "Sea View, Pool, Spa, Fine Dining", "description": "Iconic heritage hotel at Gateway of India"},
    {"name": "The Oberoi Mumbai",          "city": "Mumbai",    "price_per_night": 17000, "rating": 4.8, "amenities": "Sea View, Pool, Spa, WiFi", "description": "Luxury high-rise on Marine Drive"},
    {"name": "Ibis Mumbai Vikhroli",       "city": "Mumbai",    "price_per_night": 3200,  "rating": 4.1, "amenities": "Free WiFi, Restaurant, AC", "description": "Budget-friendly smart hotel in Vikhroli"},
    # Bangalore
    {"name": "The Ritz-Carlton Bangalore", "city": "Bangalore", "price_per_night": 16000, "rating": 4.7, "amenities": "Pool, Spa, Gym, WiFi, Fine Dining", "description": "Luxury hotel in the heart of Bangalore"},
    {"name": "Taj MG Road Bengaluru",      "city": "Bangalore", "price_per_night": 10000, "rating": 4.5, "amenities": "Pool, Spa, Multiple Restaurants", "description": "Premium hotel on iconic MG Road"},
    {"name": "Treebo Trend Maple",         "city": "Bangalore", "price_per_night": 2500,  "rating": 4.0, "amenities": "Free WiFi, AC, 24h Front Desk", "description": "Comfortable stay near Koramangala"},
    # Goa
    {"name": "Taj Exotica Goa",            "city": "Goa",       "price_per_night": 20000, "rating": 4.9, "amenities": "Private Beach, Pool, Spa, Watersports", "description": "Beachfront luxury resort in South Goa"},
    {"name": "Radisson Blu Cavelossim",    "city": "Goa",       "price_per_night": 8000,  "rating": 4.4, "amenities": "Beach Access, Pool, Bar, WiFi", "description": "Resort-style stay on Cavelossim beach"},
    {"name": "OYO Rooms Baga Beach",       "city": "Goa",       "price_per_night": 1800,  "rating": 3.8, "amenities": "WiFi, AC, Near Beach", "description": "Budget stay 5 min walk from Baga Beach"},
    # Jaipur
    {"name": "Rambagh Palace Jaipur",      "city": "Jaipur",    "price_per_night": 25000, "rating": 4.9, "amenities": "Heritage Pool, Spa, Polo, Fine Dining", "description": "Former royal palace, now a luxury hotel"},
    {"name": "ITC Rajputana Jaipur",       "city": "Jaipur",    "price_per_night": 9000,  "rating": 4.5, "amenities": "Pool, Spa, Cultural Programmes", "description": "Rajasthani heritage-themed luxury hotel"},
    {"name": "Zostel Jaipur",              "city": "Jaipur",    "price_per_night": 800,   "rating": 4.2, "amenities": "Dorm & Private Rooms, WiFi, Common Room", "description": "Social backpacker hostel near Hawa Mahal"},
    # Hyderabad
    {"name": "Taj Falaknuma Palace",       "city": "Hyderabad", "price_per_night": 30000, "rating": 4.9, "amenities": "Palace Stay, Spa, Heritage Tour, Pool", "description": "A Nizam's palace perched on a hilltop"},
    {"name": "Novotel Hyderabad Airport",  "city": "Hyderabad", "price_per_night": 6500,  "rating": 4.4, "amenities": "Pool, Spa, Free WiFi, Shuttle", "description": "5-min drive from Rajiv Gandhi Airport"},
    # Chennai
    {"name": "ITC Grand Chola Chennai",    "city": "Chennai",   "price_per_night": 12000, "rating": 4.7, "amenities": "Multiple Pools, Spa, Fine Dining, Gym", "description": "Largest hotel in South India"},
    {"name": "The Raintree Hotel Chennai", "city": "Chennai",   "price_per_night": 5500,  "rating": 4.3, "amenities": "Pool, Restaurant, WiFi, AC", "description": "Eco-friendly boutique hotel in Anna Salai"},
    # Kolkata
    {"name": "The Oberoi Grand Kolkata",   "city": "Kolkata",   "price_per_night": 11000, "rating": 4.7, "amenities": "Pool, Spa, WiFi, Heritage Architecture", "description": "Colonial landmark on Jawaharlal Nehru Road"},
    {"name": "Lemon Tree Hotel Kolkata",   "city": "Kolkata",   "price_per_night": 3800,  "rating": 4.2, "amenities": "Restaurant, WiFi, AC, Bar", "description": "Contemporary hotel near New Town"},
    # Agra
    {"name": "The Oberoi Amarvilas Agra",  "city": "Agra",      "price_per_night": 45000, "rating": 5.0, "amenities": "Taj View, Pool, Spa, Butler Service", "description": "Every room has a Taj Mahal view"},
    {"name": "Clarks Shiraz Hotel Agra",   "city": "Agra",      "price_per_night": 4500,  "rating": 4.1, "amenities": "Pool, Restaurant, WiFi, Taj View Rooftop", "description": "Classic hotel with rooftop Taj views"},
    # Pune
    {"name": "JW Marriott Pune",              "city": "Pune",     "price_per_night": 9500,  "rating": 4.7, "amenities": "Pool, Spa, 5 Restaurants, Gym, WiFi", "description": "Luxury hotel in Senapati Bapat Road"},
    {"name": "Hotel Shreyas Pune",            "city": "Pune",     "price_per_night": 2200,  "rating": 4.0, "amenities": "Restaurant, WiFi, AC, Parking", "description": "Clean mid-range stay near Shivaji Nagar"},
    # Jodhpur
    {"name": "Umaid Bhawan Palace Jodhpur",   "city": "Jodhpur",  "price_per_night": 35000, "rating": 4.9, "amenities": "Heritage Pool, Spa, Museum, Fine Dining, Butler", "description": "World's largest private residence turned luxury hotel"},
    {"name": "Taj Hari Mahal Jodhpur",        "city": "Jodhpur",  "price_per_night": 12000, "rating": 4.6, "amenities": "Pool, Spa, Rajasthani Dining, WiFi", "description": "Palatial 5-star hotel in the heart of Jodhpur"},
    {"name": "Raas Jodhpur",                  "city": "Jodhpur",  "price_per_night": 18000, "rating": 4.8, "amenities": "Rooftop Pool, Mehrangarh Fort View, Spa, Fine Dining", "description": "Luxury boutique with stunning fort views"},
    {"name": "Hotel Haveli Inn Pal Jodhpur",  "city": "Jodhpur",  "price_per_night": 3500,  "rating": 4.3, "amenities": "Rooftop Restaurant, WiFi, Fort View, AC", "description": "Charming heritage haveli near Mehrangarh Fort"},
    {"name": "Gorband Palace Jodhpur",        "city": "Jodhpur",  "price_per_night": 5500,  "rating": 4.4, "amenities": "Heritage Pool, Garden, Restaurant, WiFi", "description": "Royal heritage hotel with desert ambience"},
]

# ── Firestore Helpers ─────────────────────────────────────────────────────────
def get_user(phone: str) -> dict:
    if not db:
        return {}
    try:
        doc = db.collection("users").document(phone).get()
        return doc.to_dict() if doc.exists else {}
    except Exception as e:
        logger.error(f"get_user error: {e}")
        return {}

def update_user(phone: str, data: dict):
    if not db:
        return
    try:
        db.collection("users").document(phone).set(data, merge=True)
    except Exception as e:
        logger.error(f"update_user error: {e}")

def clear_user_state(phone: str):
    if not db:
        return
    try:
        db.collection("users").document(phone).delete()
    except Exception as e:
        logger.error(f"clear_user_state error: {e}")

def get_hotels_by_city(city: str) -> list:
    """Query Firestore hotels collection by city (case-insensitive)."""
    if not db:
        return []
    try:
        docs = db.collection("hotels").where("city_lower", "==", city.lower()).stream()
        hotels = []
        for i, doc in enumerate(docs, start=1):
            h = doc.to_dict()
            h["id"] = doc.id
            h["display_id"] = str(i)
            hotels.append(h)
        return hotels
    except Exception as e:
        logger.error(f"get_hotels_by_city error: {e}")
        return []

def save_booking(phone: str, hotel: dict, user_state: dict) -> str:
    """Save confirmed booking to Firestore bookings collection. Returns booking ID."""
    if not db:
        return "N/A"
    try:
        booking_id = str(uuid.uuid4())[:8].upper()
        checkin  = user_state.get("checkin", "")
        checkout = user_state.get("checkout", "")
        rooms    = int(user_state.get("rooms", 1))
        price    = hotel.get("price_per_night", 0)

        # Calculate nights
        nights = 1
        try:
            d1 = datetime.strptime(checkin, "%Y-%m-%d")
            d2 = datetime.strptime(checkout, "%Y-%m-%d")
            nights = max((d2 - d1).days, 1)
        except Exception:
            pass

        total = price * rooms * nights

        booking = {
            "booking_id":      booking_id,
            "phone":           phone,
            "guest_name":      user_state.get("guest_name", "N/A"),
            "guest_email":     user_state.get("guest_email", "N/A"),
            "hotel_id":        hotel.get("id"),
            "hotel_name":      hotel.get("name"),
            "city":            hotel.get("city"),
            "checkin":         checkin,
            "checkout":        checkout,
            "rooms":           rooms,
            "nights":          nights,
            "price_per_night": price,
            "total_price":     total,
            "status":          "confirmed",
            "created_at":      datetime.utcnow().isoformat(),
        }
        db.collection("bookings").document(booking_id).set(booking)
        logger.info(f"Booking saved: {booking_id}")
        return booking_id, total, nights
    except Exception as e:
        logger.error(f"save_booking error: {e}")
        return "N/A", 0, 1

# ── AI + Fallback ─────────────────────────────────────────────────────────────
# Canonical city name map (handles alternate spellings + case)
CITY_ALIASES = {
    "delhi": "Delhi", "new delhi": "Delhi",
    "mumbai": "Mumbai", "bombay": "Mumbai",
    "bangalore": "Bangalore", "bengaluru": "Bangalore", "bengaluru": "Bangalore",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai", "madras": "Chennai",
    "kolkata": "Kolkata", "calcutta": "Kolkata",
    "pune": "Pune",
    "jaipur": "Jaipur",
    "goa": "Goa",
    "agra": "Agra",
    "varanasi": "Varanasi", "banaras": "Varanasi",
    "ahmedabad": "Ahmedabad",
    "surat": "Surat",
    "lucknow": "Lucknow",
    "jodhpur": "Jodhpur",
}

def normalize_city(raw: str) -> str:
    """Return canonical city name regardless of input case/spelling."""
    if not raw:
        return ""
    key = raw.strip().lower()
    return CITY_ALIASES.get(key, raw.strip().title())

def keyword_fallback(user_message: str, user_state: dict = None) -> dict:
    result = {}
    msg = user_message.lower()
    for alias in CITY_ALIASES:
        if alias in msg:
            result["city"] = CITY_ALIASES[alias]
            break
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', user_message)
    if len(dates) >= 2:
        result["checkin"], result["checkout"] = dates[0], dates[1]
    elif len(dates) == 1:
        # Context-aware: if checkin already known, this single date must be checkout
        if user_state and user_state.get("checkin") and not user_state.get("checkout"):
            result["checkout"] = dates[0]
        else:
            result["checkin"] = dates[0]
    m = re.search(r'(\d+)\s*room', msg)
    if m:
        result["rooms"] = int(m.group(1))

    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', msg)
    if email_match:
        result["guest_email"] = email_match.group(0)

    # If we are explicitly waiting for a name and nothing else matched, treat the whole message as the name
    if user_state and user_state.get("city") and user_state.get("checkout") and not user_state.get("guest_name"):
        # Very basic heuristic: if it's not a date, not an email, not a number, it's probably the name
        if not email_match and not dates and not m:
            result["guest_name"] = user_message.strip().title()

    return result

def extract_intent(user_message: str, user_state: dict = None) -> dict:
    if not gemini_model:
        return keyword_fallback(user_message, user_state=user_state)
    prompt = f"""
    You are an AI assistant for a hotel booking system.
    Extract info from the user's message and return ONLY a raw JSON object.
    Format:
    {{
        "intent": "book_hotel",
        "city": "city name or null",
        "checkin": "YYYY-MM-DD or null",
        "checkout": "YYYY-MM-DD or null",
        "rooms": 1,
        "guest_name": "person's full name or null",
        "guest_email": "email address or null"
    }}
    User Message: "{user_message}"
    """
    for attempt in range(2):
        try:
            resp = gemini_model.generate_content(prompt)
            text = resp.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
            s, e = text.find("{"), text.rfind("}")
            if s != -1 and e != -1:
                text = text[s:e+1]
            return json.loads(text)
        except Exception as ex:
            if "429" in str(ex) and attempt == 0:
                logger.warning("Gemini 429, waiting 60s...")
                time.sleep(60)
                continue
            logger.error(f"Gemini error: {ex}")
            return keyword_fallback(user_message)
    return keyword_fallback(user_message)

def send_message(phone: str, text: str):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        logger.error("Missing WhatsApp credentials.")
        return
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    try:
        r = requests.post(url, headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }, json={
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": text}
        })
        r.raise_for_status()
        logger.info(f"Message sent to {phone}")
    except Exception as e:
        logger.error(f"send_message error: {e} | response: {getattr(e, 'response', {}).text if hasattr(e, 'response') else ''}")

def send_list_message(phone: str, body_text: str, button_text: str, sections: list):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        return
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
    }
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}, json=payload)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"send_list_message error: {e} | response: {getattr(e, 'response', {}).text if hasattr(e, 'response') else ''}")

def upload_media_to_whatsapp(filepath: str) -> str:
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/media"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (os.path.basename(filepath), f, 'application/pdf')}
            data = {'messaging_product': 'whatsapp'}
            r = requests.post(url, headers=headers, files=files, data=data)
            r.raise_for_status()
            return r.json().get("id")
    except Exception as e:
        logger.error(f"upload_media error: {e}")
        return None

def send_document_message(phone: str, media_id: str, filename: str):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "document",
        "document": {
            "id": media_id,
            "filename": filename
        }
    }
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}, json=payload)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"send_document error: {e}")

# ── Core Chat Logic ───────────────────────────────────────────────────────────
def process_message(phone: str, text: str):
    user_state = get_user(phone)
    text_clean = text.strip()

    # ── State: awaiting hotel selection ──────────────────────────────────────
    if user_state.get("state") == "awaiting_selection":
        available_hotels = user_state.get("available_hotels", [])
        selected = None

        # Match by display ID (1, 2, 3…) or hotel name (truncated or full)
        for hotel in available_hotels:
            if (hotel.get("display_id") == text_clean or
                    text_clean.lower() in hotel.get("name", "").lower() or
                    hotel.get("name", "").lower() in text_clean.lower()):
                selected = hotel
                break

        if not selected:
            send_message(phone, "❓ Please reply with the hotel number (e.g. *1*, *2*, *3*) shown in the list.")
            return

        # Save booking to Firestore
        booking_id, total, nights = save_booking(phone, selected, user_state)

        confirmation = (
            f"✅ *Booking Confirmed!*\n\n"
            f"📋 Booking ID: *{booking_id}*\n"
            f"👤 Guest: {user_state.get('guest_name', 'N/A')}\n"
            f"📧 Email: {user_state.get('guest_email', 'N/A')}\n"
            f"🏨 Hotel: {selected['name']}\n"
            f"📍 City: {selected['city']}\n"
            f"⭐ Rating: {selected.get('rating', 'N/A')}/5\n"
            f"📅 Check-in: {user_state.get('checkin')}\n"
            f"📅 Check-out: {user_state.get('checkout')}\n"
            f"🛏️ Rooms: {user_state.get('rooms', 1)} × {nights} night(s)\n"
            f"💰 Price/Night: ₹{selected.get('price_per_night', 0):,}\n"
            f"💵 Total: ₹{total:,}\n\n"
            f"Generating your receipt... 📄"
        )
        send_message(phone, confirmation)
        
        # Generate and Send PDF
        filepath = f"/tmp/receipt_{booking_id}.pdf"
        booking_data = {
            "booking_id": booking_id,
            "guest_name": user_state.get("guest_name"),
            "guest_email": user_state.get("guest_email"),
            "phone": phone,
            "hotel_name": selected["name"],
            "city": selected["city"],
            "checkin": user_state.get("checkin"),
            "checkout": user_state.get("checkout"),
            "rooms": user_state.get("rooms", 1),
            "nights": nights,
            "price_per_night": selected.get("price_per_night", 0),
            "total_price": total,
            "created_at": datetime.utcnow().isoformat()
        }
        generate_receipt(booking_data, filepath)
        
        media_id = upload_media_to_whatsapp(filepath)
        if media_id:
            send_document_message(phone, media_id, f"HotelBot_Receipt_{booking_id}.pdf")
            
        try:
            os.remove(filepath)
        except:
            pass

        clear_user_state(phone)
        return

    # ── Reset / Menu command ──────────────────────────────────────────────────
    if text_clean.lower() in ["menu", "restart", "reset", "start", "hi", "hello", "hey"]:
        clear_user_state(phone)
        send_message(phone,
            "👋 Welcome to *HotelBot*!\n\n"
            "I can help you find and book hotels across India.\n\n"
            "🏙️ Available cities: Delhi, Mumbai, Bangalore, Goa, Jaipur, Jodhpur, "
            "Hyderabad, Chennai, Kolkata, Agra, Pune\n\n"
            "Just tell me where you'd like to stay and your dates!\n"
            "_(Type city name in any case — JODHPUR, jodhpur, Jodhpur all work!)_\n\n"
            "Example: _Hotel in jodhpur from 2025-12-20 to 2025-12-25_"
        )
        return

    # ── Extract intent & merge state ─────────────────────────────────────────
    extracted = extract_intent(text_clean, user_state=user_state)

    # Context-aware date fix: if Gemini returns checkin but we already have checkin
    # and are waiting for checkout, treat it as checkout
    if (extracted.get("checkin") and not extracted.get("checkout")
            and user_state.get("checkin") and not user_state.get("checkout")):
        extracted["checkout"] = extracted.pop("checkin")

    # Context-aware extraction for name and email: if we are waiting for these, take them directly
    if user_state.get("checkout") and not user_state.get("guest_name"):
        if not re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text_clean):
            extracted["guest_name"] = text_clean.strip().title()
            
    if user_state.get("guest_name") and not user_state.get("guest_email"):
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text_clean)
        if email_match:
            extracted["guest_email"] = email_match.group(0)

    for key in ["city", "checkin", "checkout", "rooms", "guest_name", "guest_email"]:
        val = extracted.get(key)
        if val and val not in (None, "null", "None", ""):
            if key == "city":
                val = normalize_city(str(val))
            user_state[key] = val

    update_user(phone, user_state)

    # ── Decision Engine ───────────────────────────────────────────────────────
    if not user_state.get("city"):
        sections = [
            {
                "title": "Top Destinations",
                "rows": [
                    {"id": "city_delhi", "title": "Delhi"},
                    {"id": "city_mumbai", "title": "Mumbai"},
                    {"id": "city_bangalore", "title": "Bangalore"},
                    {"id": "city_goa", "title": "Goa"},
                    {"id": "city_jaipur", "title": "Jaipur"},
                    {"id": "city_jodhpur", "title": "Jodhpur"}
                ]
            },
            {
                "title": "Other Cities",
                "rows": [
                    {"id": "city_hyderabad", "title": "Hyderabad"},
                    {"id": "city_chennai", "title": "Chennai"},
                    {"id": "city_kolkata", "title": "Kolkata"},
                    {"id": "city_agra", "title": "Agra"},
                    {"id": "city_pune", "title": "Pune"}
                ]
            }
        ]
        send_list_message(
            phone,
            "🏙️ Which city would you like to book a hotel in?\nTap the button below to select.",
            "Choose City",
            sections
        )
        return

    if not user_state.get("checkin"):
        send_message(phone, f"📅 Check-in date for *{user_state['city']}*? (Format: YYYY-MM-DD)")
        return

    if not user_state.get("checkout"):
        send_message(phone, f"📅 Check-out date? (Format: YYYY-MM-DD)")
        return

    if not user_state.get("rooms"):
        user_state["rooms"] = 1

    if not user_state.get("guest_name"):
        send_message(phone, "👤 What is your full name for the booking?")
        return
        
    if not user_state.get("guest_email"):
        send_message(phone, "📧 What is your email address to send the receipt?")
        return

    # ── Fetch real hotels from Firestore ──────────────────────────────────────
    city = user_state["city"]
    hotels = get_hotels_by_city(city)

    if not hotels:
        send_message(phone,
            f"😔 Sorry, no hotels found in *{city}* right now.\n"
            "Try another city like Goa, Delhi, or Mumbai."
        )
        user_state.pop("city", None)
        update_user(phone, user_state)
        return

    # Attach display IDs and store in user state for selection matching
    for i, h in enumerate(hotels, start=1):
        h["display_id"] = str(i)

    user_state["state"] = "awaiting_selection"
    user_state["available_hotels"] = hotels
    update_user(phone, user_state)

    hotels_text = (
        f"🏨 *Hotels in {city}*\n"
        f"📅 {user_state['checkin']} → {user_state['checkout']} | 🛏️ {user_state.get('rooms', 1)} room(s)\n"
    )
    
    hotel_rows = []
    for h in hotels[:10]: # WhatsApp max is 10 rows
        desc = f"₹{h.get('price_per_night', 0):,}/night | ⭐{h.get('rating', 'N/A')}"
        hotel_rows.append({
            "id": f"hotel_{h['display_id']}",
            "title": h['name'][:24], # title max length 24 chars
            "description": desc[:72] # description max length 72 chars
        })
    
    sections = [{"title": "Available Hotels", "rows": hotel_rows}]
    send_list_message(phone, hotels_text, "View Hotels", sections)

# ── Admin: Seed Hotels ────────────────────────────────────────────────────────
@app.post("/admin/seed-hotels")
async def seed_hotels():
    """Populate Firestore with real hotel data. Run once."""
    if not db:
        return {"error": "Firestore not connected"}
    count = 0
    for hotel in SEED_HOTELS:
        doc_id = hotel["name"].lower().replace(" ", "_").replace(",", "")
        data = {**hotel, "city_lower": hotel["city"].lower(), "available": True}
        db.collection("hotels").document(doc_id).set(data)
        count += 1
    return {"status": "ok", "seeded": count, "message": f"{count} hotels added to Firestore"}

@app.get("/admin/bookings")
async def list_bookings():
    """View all bookings in Firestore."""
    if not db:
        return {"error": "Firestore not connected"}
    try:
        docs = db.collection("bookings").order_by("created_at", direction=firestore.Query.DESCENDING).limit(50).stream()
        return {"bookings": [d.to_dict() for d in docs]}
    except Exception as e:
        return {"error": str(e)}

@app.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin Dashboard UI"""
    if not db:
        return "Firestore not connected"
    
    # Get bookings
    b_docs = db.collection("bookings").order_by("created_at", direction=firestore.Query.DESCENDING).limit(100).stream()
    bookings = [d.to_dict() for d in b_docs]
    
    # Calculate stats
    total_bookings = len(bookings)
    total_revenue = sum(b.get("total_price", 0) for b in bookings)
    
    # Get hotels count
    h_docs = db.collection("hotels").stream()
    total_hotels = len(list(h_docs))
    
    stats = {
        "total_bookings": total_bookings,
        "total_revenue": total_revenue,
        "total_hotels": total_hotels
    }
    
    return templates.TemplateResponse("dashboard.html", {"request": request, "bookings": bookings, "stats": stats})

@app.get("/admin/hotels")
async def list_hotels():
    """View all hotels in Firestore."""
    if not db:
        return {"error": "Firestore not connected"}
    try:
        docs = db.collection("hotels").stream()
        return {"hotels": [d.to_dict() for d in docs]}
    except Exception as e:
        return {"error": str(e)}

# ── Webhook ───────────────────────────────────────────────────────────────────
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode      = request.query_params.get("hub.mode")
    token     = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)

@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        # Only log actual user messages, not delivery receipts/status updates
        has_messages = any(
            change.get("value", {}).get("messages")
            for entry in body.get("entry", [])
            for change in entry.get("changes", [])
        )
        if has_messages:
            logger.info(f"Incoming message: {json.dumps(body)}")
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    for msg in change.get("value", {}).get("messages", []):
                        if msg.get("type") == "text":
                            text = msg.get("text", {}).get("body", "")
                            background_tasks.add_task(process_message, msg.get("from"), text)
                        elif msg.get("type") == "interactive":
                            interactive = msg.get("interactive", {})
                            if interactive.get("type") == "list_reply":
                                text = interactive.get("list_reply", {}).get("title", "")
                                background_tasks.add_task(process_message, msg.get("from"), text)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status_code=500)

@app.get("/")
async def root():
    return {"status": "HotelBot running", "firestore": db is not None, "gemini": gemini_model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

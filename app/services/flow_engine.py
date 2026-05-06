import logging
from app.db.firebase import get_db
from app.services.whatsapp import whatsapp_service
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# State constants
STAGE_GREETING = "GREETING"
STAGE_CITY_SELECT = "CITY_SELECT"
STAGE_HOTEL_SELECT = "HOTEL_SELECT"
STAGE_CHECKIN_MONTH = "CHECKIN_MONTH"
STAGE_CHECKIN_DAY = "CHECKIN_DAY"
STAGE_CHECKOUT_DUR = "CHECKOUT_DUR"
STAGE_GUEST_NAME = "GUEST_NAME"
STAGE_GUEST_EMAIL = "GUEST_EMAIL"
STAGE_PAYMENT = "PAYMENT"
STAGE_CONFIRMED = "CONFIRMED"

def get_user_state(phone: str) -> dict:
    db = get_db()
    if not db: return {"stage": STAGE_GREETING}
    try:
        doc = db.collection("users_state").document(phone).get()
        return doc.to_dict() if doc.exists else {"stage": STAGE_GREETING}
    except Exception as e:
        logger.error(f"get_user_state error: {e}")
        return {"stage": STAGE_GREETING}

def update_user_state(phone: str, data: dict):
    db = get_db()
    if not db: return
    try:
        db.collection("users_state").document(phone).set(data, merge=True)
    except Exception as e:
        logger.error(f"update_user_state error: {e}")

def clear_user_state(phone: str):
    db = get_db()
    if not db: return
    try:
        db.collection("users_state").document(phone).delete()
    except Exception as e:
        logger.error(f"clear_user_state error: {e}")

# Fetch data from DB
def get_available_cities():
    db = get_db()
    if not db: return ["Jaipur", "Mumbai", "Goa", "Delhi", "Udaipur"]
    try:
        # Get unique cities from all hotels
        docs = db.collection("hotels").stream()
        cities = set()
        for d in docs:
            city = d.to_dict().get("city")
            if city:
                cities.add(city.title())
        # Return sorted list, or fallback if empty
        return sorted(list(cities)) if cities else ["Jaipur", "Mumbai", "Goa", "Delhi", "Udaipur"]
    except Exception as e:
        logger.error(f"get_available_cities error: {e}")
        return ["Jaipur", "Mumbai", "Goa", "Delhi", "Udaipur"]

def get_hotels_in_city(city: str):
    db = get_db()
    if not db: return []
    try:
        # Case insensitive city query can be tricky in Firestore, we'll fetch and filter
        # Or assuming cities are saved consistently (e.g. title case)
        docs = db.collection("hotels").where("city", "==", city).stream()
        hotels = []
        for d in docs:
            data = d.to_dict()
            hotels.append({
                "id": d.id,
                "name": data.get("name", "Unknown Hotel"),
                "price": data.get("price_per_night", 2000),
                "rating": data.get("rating", 4.0),
                "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80" # placeholder for now
            })
        return hotels
    except Exception as e:
        logger.error(f"get_hotels_in_city error: {e}")
        return []

def generate_month_options():
    sections = [{"title": "Select Month", "rows": []}]
    now = datetime.now()
    for i in range(5):
        d = now + timedelta(days=30*i)
        month_str = d.strftime("%Y-%m")
        display = d.strftime("%B %Y")
        sections[0]["rows"].append({"id": f"month_{month_str}", "title": display})
    return sections

def generate_day_options(month_str):
    # Just a simple approximation for demo
    sections = [{"title": "Select Day", "rows": []}]
    try:
        y, m = map(int, month_str.split('-'))
        # Generate some quick options
        for day in [1, 5, 10, 15, 20, 25, 28]:
            sections[0]["rows"].append({"id": f"day_{y}-{m:02d}-{day:02d}", "title": f"{day} {datetime(y, m, day).strftime('%B')}"})
    except:
        pass
    return sections

def handle_interactive_flow(phone: str, text: str, payload_id: str = None):
    """
    Main state machine for processing WhatsApp messages.
    text: the display text sent by the user
    payload_id: the hidden ID from a button or list selection
    """
    text_clean = text.strip()
    user_state = get_user_state(phone)
    current_stage = user_state.get("stage", STAGE_GREETING)

    logger.info(f"Flow Engine [{phone}]: Stage={current_stage}, Text={text_clean}, Payload={payload_id}")

    # Global reset
    GREETINGS = ["hi", "hii", "hiii", "hello", "helo", "hey", "heyy", "yo", "menu", "restart", "reset", "start"]
    if text_clean.lower() in GREETINGS:
        clear_user_state(phone)
        user_state = {"stage": STAGE_CITY_SELECT}
        update_user_state(phone, user_state)
        
        # Send greeting with buttons
        whatsapp_service.send_button_message(
            phone,
            "👋 *Welcome to HotelBot!*\n\nI can help you find and book the perfect stay.",
            [
                {"id": "action_book", "title": "Book Hotel"},
                {"id": "action_offers", "title": "View Offers"},
                {"id": "action_support", "title": "Support"}
            ]
        )
        return

    # Handle actions from the main menu
    if payload_id == "action_offers":
        whatsapp_service.send_message(phone, "🎉 Current offers:\n- 20% off in Jaipur!\n- Free breakfast in Goa.")
        return
    if payload_id == "action_support":
        whatsapp_service.send_message(phone, "📞 Please call +91-800-HOTEL-BOT for support.")
        return

    # ---------------------------------------------------------
    # STAGE: CITY SELECT
    # ---------------------------------------------------------
    if current_stage == STAGE_CITY_SELECT or payload_id == "action_book":
        cities = get_available_cities()[:10]  # WhatsApp limits list rows to 10 max
        sections = [{"title": "Popular Cities", "rows": []}]
        for city in cities:
            title = city[:24]
            desc = f"View hotels in {city}"[:72]
            sections[0]["rows"].append({"id": f"city_{city}", "title": title, "description": desc})
            
        whatsapp_service.send_list_message(
            phone,
            "🏙️ *Where would you like to go?*\n\nPlease select a city from the list below.",
            "Choose City",
            sections
        )
        user_state["stage"] = STAGE_HOTEL_SELECT
        update_user_state(phone, user_state)
        return

    # ---------------------------------------------------------
    # STAGE: HOTEL SELECT
    # ---------------------------------------------------------
    if current_stage == STAGE_HOTEL_SELECT:
        if payload_id and payload_id.startswith("city_"):
            city = payload_id.replace("city_", "")
            user_state["city"] = city
            update_user_state(phone, user_state)
        else:
            city = user_state.get("city")
            if not city:
                whatsapp_service.send_message(phone, "Please select a city first.")
                return

        hotels = get_hotels_in_city(city)
        # WhatsApp limits list rows to 10 max
        if len(hotels) > 10:
            whatsapp_service.send_message(phone, f"🔍 Found {len(hotels)} hotels in *{city}*. Showing top 10:")
            hotels = hotels[:10]
        else:
            whatsapp_service.send_message(phone, f"🔍 Found {len(hotels)} hotels in *{city}*:")
        
        for h in hotels:
            whatsapp_service.send_image_message(phone, h["image"], f"🏨 *{h['name']}*\n⭐ {h['rating']} Stars\n💰 ₹{h['price']} per night")
            
        # Send selection list
        sections = [{"title": "Available Hotels", "rows": []}]
        for h in hotels:
            title = h['name'][:24] # WhatsApp limit is 24 characters for list row title
            sections[0]["rows"].append({
                "id": f"hotel_{h['id']}", 
                "title": title, 
                "description": f"₹{h['price']}/night"
            })
            
        whatsapp_service.send_list_message(
            phone,
            "Select your preferred hotel to continue:",
            "View Hotels",
            sections
        )
        user_state["stage"] = STAGE_CHECKIN_MONTH
        update_user_state(phone, user_state)
        return

    # ---------------------------------------------------------
    # STAGE: CHECKIN MONTH
    # ---------------------------------------------------------
    if current_stage == STAGE_CHECKIN_MONTH:
        if payload_id and payload_id.startswith("hotel_"):
            hotel_id = payload_id.replace("hotel_", "")
            user_state["hotel_id"] = hotel_id
            update_user_state(phone, user_state)
            
        sections = generate_month_options()
        whatsapp_service.send_list_message(
            phone,
            "📅 *When would you like to check in?*\nFirst, select the month:",
            "Select Month",
            sections
        )
        user_state["stage"] = STAGE_CHECKIN_DAY
        update_user_state(phone, user_state)
        return

    # ---------------------------------------------------------
    # STAGE: CHECKIN DAY
    # ---------------------------------------------------------
    if current_stage == STAGE_CHECKIN_DAY:
        if payload_id and payload_id.startswith("month_"):
            month_str = payload_id.replace("month_", "")
            sections = generate_day_options(month_str)
            whatsapp_service.send_list_message(
                phone,
                "📅 Now select the *Check-in Date*:",
                "Select Date",
                sections
            )
            user_state["stage"] = STAGE_CHECKOUT_DUR
            update_user_state(phone, user_state)
            return
        else:
            whatsapp_service.send_message(phone, "Please use the menu to select a month.")
            return

    # ---------------------------------------------------------
    # STAGE: CHECKOUT (Duration)
    # ---------------------------------------------------------
    if current_stage == STAGE_CHECKOUT_DUR:
        if payload_id and payload_id.startswith("day_"):
            date_str = payload_id.replace("day_", "")
            user_state["checkin"] = date_str
            update_user_state(phone, user_state)
            
            whatsapp_service.send_button_message(
                phone,
                f"Your check-in is set to *{date_str}*.\n\nHow many nights will you stay?",
                [
                    {"id": "nights_1", "title": "1 Night"},
                    {"id": "nights_2", "title": "2 Nights"},
                    {"id": "nights_3", "title": "3+ Nights"}
                ]
            )
            user_state["stage"] = STAGE_GUEST_NAME
            update_user_state(phone, user_state)
            return

    # ---------------------------------------------------------
    # STAGE: GUEST NAME
    # ---------------------------------------------------------
    if current_stage == STAGE_GUEST_NAME:
        if payload_id and payload_id.startswith("nights_"):
            nights = payload_id.replace("nights_", "")
            user_state["nights"] = nights
            update_user_state(phone, user_state)
            
            whatsapp_service.send_message(phone, "👤 *Almost done!*\nPlease type your full name:")
            user_state["stage"] = STAGE_GUEST_EMAIL
            update_user_state(phone, user_state)
            return

    # ---------------------------------------------------------
    # STAGE: GUEST EMAIL
    # ---------------------------------------------------------
    if current_stage == STAGE_GUEST_EMAIL:
        user_state["guest_name"] = text_clean
        update_user_state(phone, user_state)
        
        whatsapp_service.send_message(phone, "✉️ Please type your email address (for the receipt):")
        user_state["stage"] = STAGE_PAYMENT
        update_user_state(phone, user_state)
        return

    # ---------------------------------------------------------
    # STAGE: PAYMENT / CONFIRMATION
    # ---------------------------------------------------------
    if current_stage == STAGE_PAYMENT:
        user_state["guest_email"] = text_clean
        update_user_state(phone, user_state)
        
        # Summary
        msg = f"✅ *Booking Summary*\n\n"
        msg += f"🏙️ City: {user_state.get('city')}\n"
        msg += f"📅 Check-in: {user_state.get('checkin')}\n"
        msg += f"🌙 Nights: {user_state.get('nights')}\n"
        msg += f"👤 Guest: {user_state.get('guest_name')}\n"
        msg += f"✉️ Email: {user_state.get('guest_email')}\n\n"
        msg += f"Please confirm your booking."
        
        whatsapp_service.send_button_message(
            phone,
            msg,
            [
                {"id": "confirm_book", "title": "Confirm & Pay"},
                {"id": "cancel_book", "title": "Cancel"}
            ]
        )
        user_state["stage"] = STAGE_CONFIRMED
        update_user_state(phone, user_state)
        return

    if current_stage == STAGE_CONFIRMED:
        if payload_id == "confirm_book":
            whatsapp_service.send_message(phone, "⏳ Generating payment link...")
            
            # Use real hotel price if available, else default
            amount = 2000
            try:
                if "hotel_id" in user_state:
                    hotels = get_hotels_in_city(user_state.get("city", ""))
                    for h in hotels:
                        if h["id"] == user_state["hotel_id"]:
                            amount = h.get("price", 2000)
                            break
            except:
                pass
            
            total_amount = amount * int(user_state.get("nights", 1))
            
            from app.services.payment import create_payment_link
            payment_res = create_payment_link(
                amount=total_amount,
                currency="INR",
                description=f"Booking for {user_state.get('nights')} nights at {user_state.get('city')}",
                customer_name=user_state.get("guest_name"),
                customer_email=user_state.get("guest_email"),
                customer_phone=phone,
                reference_id=phone
            )
            
            if payment_res and payment_res.get("url"):
                whatsapp_service.send_message(phone, f"💳 *Please complete your payment to confirm the booking:*\n\n{payment_res['url']}\n\nThank you for choosing HotelBot!")
            else:
                whatsapp_service.send_message(phone, "💳 *[Mock Payment Link]*\n(Razorpay keys not configured)\n\nThank you for choosing HotelBot!")
                
        elif payload_id == "cancel_book":
            clear_user_state(phone)
            whatsapp_service.send_message(phone, "Booking cancelled. Type 'hi' to start over.")
        return

    # Fallback
    whatsapp_service.send_message(phone, "I didn't understand that. Type 'hi' to restart the booking flow.")

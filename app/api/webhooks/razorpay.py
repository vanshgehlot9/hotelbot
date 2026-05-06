from fastapi import APIRouter, Request, Response
import logging
from app.core.config import settings
from app.services.whatsapp import whatsapp_service
from app.db.firebase import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    try:
        body = await request.json()
        logger.info(f"Razorpay webhook received: {body}")
        
        event = body.get("event")
        payload = body.get("payload", {})
        
        if event == "payment_link.paid":
            payment_link = payload.get("payment_link", {}).get("entity", {})
            reference_id = payment_link.get("notes", {}).get("reference_id") # We stored phone number here
            amount = payment_link.get("amount", 0) / 100 # convert paise back to INR
            
            if reference_id:
                phone = reference_id
                
                # Update booking status in Firebase
                db = get_db()
                if db:
                    # Update user state
                    user_state_ref = db.collection("users_state").document(phone)
                    user_state = user_state_ref.get().to_dict() if user_state_ref.get().exists else {}
                    
                    # Create a booking record
                    booking_id = f"BK-{payment_link.get('id', 'XXX')[-6:].upper()}"
                    booking_data = {
                        "booking_id": booking_id,
                        "phone": phone,
                        "guest_name": user_state.get("guest_name"),
                        "guest_email": user_state.get("guest_email"),
                        "city": user_state.get("city"),
                        "hotel_id": user_state.get("hotel_id"),
                        "checkin": user_state.get("checkin"),
                        "nights": user_state.get("nights"),
                        "amount_paid": amount,
                        "payment_link_id": payment_link.get("id"),
                        "status": "CONFIRMED",
                        "timestamp": payment_link.get("created_at")
                    }
                    db.collection("bookings").document(booking_id).set(booking_data)
                    
                    # Send confirmation WhatsApp message
                    msg = f"🎉 *Payment Successful!*\n\n"
                    msg += f"Your booking is confirmed. Booking ID: *{booking_id}*\n"
                    msg += f"Amount paid: ₹{amount}\n\n"
                    msg += f"We are generating your invoice now. 📄"
                    whatsapp_service.send_message(phone, msg)
                    
                    # Generate PDF Receipt (Phase 4)
                    from receipt_generator import process_and_send_receipt
                    
                    # Add required fields for receipt generator
                    booking_data["total_price"] = amount
                    
                    # Get hotel name
                    hotel_name = "HotelBot Partner"
                    try:
                        hotels = db.collection("hotels").where("city", "==", user_state.get("city")).stream()
                        for h in hotels:
                            if h.id == user_state.get("hotel_id"):
                                hotel_name = h.to_dict().get("name", "HotelBot Partner")
                                break
                    except:
                        pass
                        
                    booking_data["hotel_name"] = hotel_name
                    
                    # Send receipt in background
                    import asyncio
                    asyncio.create_task(asyncio.to_thread(process_and_send_receipt, phone, booking_data))
                    
                    # Clear user state for next booking
                    user_state_ref.delete()
                    
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Razorpay webhook error: {e}")
        return Response(status_code=500)

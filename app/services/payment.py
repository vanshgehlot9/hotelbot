import razorpay
import logging
import time
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Razorpay Client
client = None
if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
else:
    logger.warning("Razorpay credentials not found in settings.")

def create_payment_link(amount: int, currency: str, description: str, customer_name: str, customer_email: str, customer_phone: str, reference_id: str):
    """
    Generate a Razorpay payment link.
    amount: Amount in INR (not paise, we will convert it here)
    """
    if not client:
        logger.error("Razorpay client is not initialized.")
        return None

    try:
        # amount is passed in INR, Razorpay expects paise (INR * 100)
        amount_in_paise = int(amount * 100)
        
        payment_link_data = {
            "amount": amount_in_paise,
            "currency": currency,
            "accept_partial": False,
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_phone
            },
            "notify": {
                "sms": False, # We will send WhatsApp instead
                "email": True
            },
            "reminder_enable": True,
            "notes": {
                "reference_id": reference_id
            },
            "callback_url": f"{settings.NGROK_URL}/webhooks/razorpay" if hasattr(settings, 'NGROK_URL') and settings.NGROK_URL else "https://yourdomain.com/webhooks/razorpay",
            "callback_method": "get"
        }
        
        # Create payment link
        payment_link = client.payment_link.create(payment_link_data)
        logger.info(f"Payment link created: {payment_link['id']}")
        
        return {
            "id": payment_link["id"],
            "url": payment_link["short_url"],
            "status": payment_link["status"]
        }
    except Exception as e:
        logger.error(f"Error creating payment link: {e}")
        return None

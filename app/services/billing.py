import razorpay
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class BillingService:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.client = None
        if self.key_id and self.key_secret and self.key_id != "mock_key_id":
            try:
                self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
            except Exception as e:
                logger.error(f"Failed to init Razorpay: {e}")

    def create_subscription(self, plan_id: str, total_count: int, customer_notify: int = 1) -> dict:
        """
        Creates a Razorpay subscription for a tenant.
        """
        if not self.client:
            logger.warning("Razorpay client not initialized. Returning mock subscription.")
            return {"id": "sub_mock123", "status": "created"}
        
        try:
            subscription = self.client.subscription.create({
                "plan_id": plan_id,
                "customer_notify": customer_notify,
                "total_count": total_count,
            })
            return subscription
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return {}

    def get_subscription(self, subscription_id: str) -> dict:
        if not self.client:
            return {"id": subscription_id, "status": "active"}
            
        try:
            return self.client.subscription.fetch(subscription_id)
        except Exception as e:
            logger.error(f"Error fetching subscription: {e}")
            return {}

billing_service = BillingService()

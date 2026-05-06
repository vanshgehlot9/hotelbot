from typing import Optional
from pydantic import BaseModel, Field

class TenantBase(BaseModel):
    name: str
    subscription_tier: str = "free" # free, pro, enterprise
    whatsapp_number_id: Optional[str] = None
    razorpay_customer_id: Optional[str] = None
    
class TenantCreate(TenantBase):
    pass

class TenantInDB(TenantBase):
    id: str

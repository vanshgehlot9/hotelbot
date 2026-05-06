from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class BookingBase(BaseModel):
    phone: str
    guest_name: str
    guest_email: str
    hotel_id: str
    hotel_name: str
    city: str
    checkin: str
    checkout: str
    rooms: int
    nights: int
    price_per_night: float
    total_price: float
    tenant_id: str
    status: str = "confirmed"

class BookingInDB(BookingBase):
    booking_id: str
    created_at: str = datetime.utcnow().isoformat()

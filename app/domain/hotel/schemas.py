from typing import Optional
from pydantic import BaseModel

class HotelBase(BaseModel):
    name: str
    city: str
    city_lower: str
    price_per_night: int
    rating: float
    amenities: str
    description: str
    tenant_id: str

class HotelInDB(HotelBase):
    id: str
    available: bool = True

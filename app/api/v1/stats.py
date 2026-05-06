from datetime import date
from fastapi import APIRouter, Depends
from app.api.dependencies import get_firestore_db, require_superadmin, require_tenant_admin, get_current_active_user

router = APIRouter()

@router.get("/superadmin")
async def get_superadmin_stats(
    db=Depends(get_firestore_db),
    current_user: dict = Depends(require_superadmin)
):
    try:
        tenants = list(db.collection("tenants").stream())
        hotels = list(db.collection("hotels").stream())
        bookings = list(db.collection("bookings").stream())
        users = list(db.collection("users").stream())
        total_revenue = sum(b.to_dict().get("total_price", 0) for b in bookings)
        return {
            "total_tenants": len(tenants),
            "total_hotels": len(hotels),
            "total_bookings": len(bookings),
            "total_revenue": total_revenue,
            "total_users": len(users),
        }
    except Exception as e:
        return {"total_tenants": 0, "total_hotels": 0, "total_bookings": 0, "total_revenue": 0, "total_users": 0, "error": str(e)}


@router.get("/tenant")
async def get_tenant_stats(
    db=Depends(get_firestore_db),
    current_user: dict = Depends(require_tenant_admin)
):
    tenant_id = current_user.get("tenant_id")
    try:
        hotels = list(db.collection("hotels").where("tenant_id", "==", tenant_id).stream())
        bookings = list(db.collection("bookings").where("tenant_id", "==", tenant_id).stream())
        booking_dicts = [b.to_dict() for b in bookings]
        total_revenue = sum(b.get("total_price", 0) for b in booking_dicts)
        agents = list(db.collection("users").where("tenant_id", "==", tenant_id).where("role", "==", "agent").stream())
        return {
            "total_hotels": len(hotels),
            "total_bookings": len(booking_dicts),
            "total_revenue": total_revenue,
            "total_agents": len(agents),
        }
    except Exception as e:
        return {"total_hotels": 0, "total_bookings": 0, "total_revenue": 0, "total_agents": 0, "error": str(e)}


@router.get("/agent")
async def get_agent_stats(
    db=Depends(get_firestore_db),
    current_user: dict = Depends(get_current_active_user)
):
    tenant_id = current_user.get("tenant_id")
    today = date.today().isoformat()

    try:
        bookings = list(db.collection("bookings").where("tenant_id", "==", tenant_id).stream())
        booking_dicts = [b.to_dict() for b in bookings]

        arrivals = [b for b in booking_dicts if b.get("checkin", "").startswith(today)]
        departures = [b for b in booking_dicts if b.get("checkout", "").startswith(today)]
        pending = [b for b in booking_dicts if b.get("status") == "confirmed" and b.get("checkin", "") > today]
        total_confirmed = len([b for b in booking_dicts if b.get("status") == "confirmed"])

        return {
            "arrivals_today": len(arrivals),
            "departures_today": len(departures),
            "pending_bookings": len(pending),
            "total_confirmed": total_confirmed,
            "todays_arrivals": arrivals[:10],
        }
    except Exception as e:
        return {
            "arrivals_today": 0,
            "departures_today": 0,
            "pending_bookings": 0,
            "total_confirmed": 0,
            "todays_arrivals": [],
            "error": str(e)
        }

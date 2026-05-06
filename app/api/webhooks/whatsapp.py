from fastapi import APIRouter, Request, Response, BackgroundTasks
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(status_code=403)

def process_whatsapp(phone: str, text: str, payload_id: str = None):
    """Process in FastAPI background thread using Flow Engine."""
    try:
        from app.services.flow_engine import handle_interactive_flow
        handle_interactive_flow(phone, text, payload_id)
    except Exception as e:
        logger.error(f"process_whatsapp error for {phone}: {e}")
        try:
            from app.services.whatsapp import whatsapp_service
            whatsapp_service.send_message(phone, "😓 Something went wrong. Type *hi* to start again.")
        except Exception:
            pass

@router.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()

        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    messages = change.get("value", {}).get("messages", [])
                    for msg in messages:
                        phone = msg.get("from")
                        text = ""
                        payload_id = None

                        if msg.get("type") == "text":
                            text = msg.get("text", {}).get("body", "")
                        elif msg.get("type") == "interactive":
                            interactive = msg.get("interactive", {})
                            if interactive.get("type") == "list_reply":
                                text = interactive.get("list_reply", {}).get("title", "")
                                payload_id = interactive.get("list_reply", {}).get("id", "")
                            elif interactive.get("type") == "button_reply":
                                text = interactive.get("button_reply", {}).get("title", "")
                                payload_id = interactive.get("button_reply", {}).get("id", "")

                        if phone:
                            background_tasks.add_task(process_whatsapp, phone, text, payload_id)

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "ok"}  # Always return 200 to WhatsApp

import requests
import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.access_token = settings.ACCESS_TOKEN
        self.phone_number_id = settings.PHONE_NUMBER_ID

    def send_message(self, phone: str, text: str):
        if not self.access_token or not self.phone_number_id:
            logger.error("Missing WhatsApp credentials.")
            return
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        try:
            r = requests.post(url, headers={
                "Authorization": f"Bearer {self.access_token}",
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
            logger.error(f"send_message error: {e}")

    def send_list_message(self, phone: str, body_text: str, button_text: str, sections: list):
        if not self.access_token or not self.phone_number_id:
            return
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
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
            r = requests.post(url, headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}, json=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"send_list_message error: {e}")

    def send_button_message(self, phone: str, body_text: str, buttons: list):
        """Sends an interactive message with up to 3 buttons.
        buttons should be a list of dicts: [{"id": "btn_1", "title": "Yes"}, ...]"""
        if not self.access_token or not self.phone_number_id:
            return
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        
        interactive_buttons = []
        for btn in buttons[:3]:  # WhatsApp limits to 3 buttons max
            interactive_buttons.append({
                "type": "reply",
                "reply": {
                    "id": btn["id"],
                    "title": btn["title"]
                }
            })
            
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": interactive_buttons
                }
            }
        }
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}, json=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"send_button_message error: {e}")

    def send_image_message(self, phone: str, image_url: str, caption: str = ""):
        if not self.access_token or not self.phone_number_id:
            return
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption
            }
        }
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}, json=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"send_image_message error: {e}")

    def upload_media(self, filepath: str) -> str:
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/media"
        headers = {"Authorization": f"Bearer {self.access_token}"}
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

    def send_document_message(self, phone: str, media_id: str, filename: str):
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
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
            r = requests.post(url, headers={"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}, json=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"send_document error: {e}")

whatsapp_service = WhatsAppService()

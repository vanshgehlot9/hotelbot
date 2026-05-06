import json
import logging
import os
import firebase_admin
from firebase_admin import credentials, firestore
from app.core.config import settings

logger = logging.getLogger(__name__)

def _parse_firebase_credentials(cred_value: str) -> dict:
    raw = (cred_value or "").strip()
    if not raw:
        raise ValueError("FIREBASE_CREDENTIALS is empty")

    if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
        raw = raw[1:-1]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    normalized = raw.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
    return json.loads(normalized)

db = None

def init_firebase():
    global db
    try:
        if not firebase_admin._apps:
            cred_value = settings.FIREBASE_CREDENTIALS
            if cred_value:
                if cred_value.strip().startswith("{"):
                    cred_dict = _parse_firebase_credentials(cred_value)
                    firebase_admin.initialize_app(credentials.Certificate(cred_dict))
                elif os.path.exists(cred_value):
                    firebase_admin.initialize_app(credentials.Certificate(cred_value))
                else:
                    logger.warning(f"Firebase creds not found or invalid format: {cred_value[:20]}...")
            else:
                logger.warning("FIREBASE_CREDENTIALS not set.")
        db = firestore.client() if firebase_admin._apps else None
    except Exception as e:
        logger.error(f"Firebase init failed: {e}")
        db = None

init_firebase()

def get_db():
    return db

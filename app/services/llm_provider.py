from abc import ABC, abstractmethod
import json
import re
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    @abstractmethod
    def extract_intent(self, user_message: str, user_state: dict = None) -> dict:
        pass

class GeminiService(LLMProvider):
    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                from google.genai import types
                self.client = genai.Client(
                    api_key=settings.GEMINI_API_KEY,
                    http_options=types.HttpOptions(timeout=5000)  # 5 second timeout, fail fast
                )
                logger.info("Gemini client initialized with google-genai SDK")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        else:
            logger.warning("GEMINI_API_KEY not set. Falling back to keyword extraction.")

    def keyword_fallback(self, user_message: str, user_state: dict = None) -> dict:
        result = {}
        msg = user_message.lower()

        # City extraction — match against common Indian cities
        INDIAN_CITIES = [
            "jaipur", "jodhpur", "udaipur", "ajmer", "kota", "bikaner",
            "mumbai", "delhi", "bangalore", "hyderabad", "chennai",
            "kolkata", "pune", "ahmedabad", "surat", "jaisalmer",
            "agra", "varanasi", "lucknow", "chandigarh", "goa",
            "manali", "shimla", "mussoorie", "haridwar", "rishikesh",
            "amritsar", "gurgaon", "noida", "indore", "bhopal"
        ]
        for city in INDIAN_CITIES:
            if city in msg:
                result["city"] = city.title()
                break

        # Date extraction
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', user_message)
        if len(dates) >= 2:
            result["checkin"], result["checkout"] = dates[0], dates[1]
        elif len(dates) == 1:
            if user_state and user_state.get("checkin") and not user_state.get("checkout"):
                result["checkout"] = dates[0]
            else:
                result["checkin"] = dates[0]

        m = re.search(r'(\d+)\s*room', msg)
        if m:
            result["rooms"] = int(m.group(1))

        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', msg)
        if email_match:
            result["guest_email"] = email_match.group(0)

        if user_state and user_state.get("city") and user_state.get("checkout") and not user_state.get("guest_name"):
            if not email_match and not dates and not m and "city" not in result:
                result["guest_name"] = user_message.strip().title()
        return result

    def extract_intent(self, user_message: str, user_state: dict = None) -> dict:
        if not self.client:
            return self.keyword_fallback(user_message, user_state)

        prompt = f"""You are an AI assistant for a hotel booking system.
Extract info from the user's message and return ONLY a raw JSON object.
Format:
{{
    "intent": "book_hotel",
    "city": "city name or null",
    "checkin": "YYYY-MM-DD or null",
    "checkout": "YYYY-MM-DD or null",
    "rooms": 1,
    "guest_name": "person's full name or null",
    "guest_email": "email address or null"
}}
User Message: "{user_message}"
Current booking state: {json.dumps(user_state or {})}"""

        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            text = response.text.strip()
            # Strip any markdown code fences
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            s, e = text.find("{"), text.rfind("}")
            if s != -1 and e != -1:
                text = text[s:e+1]
            return json.loads(text)
        except Exception as ex:
            err_str = str(ex)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                # Quota exceeded — skip immediately to keyword fallback, don't retry
                logger.warning("Gemini quota exceeded, using keyword fallback instantly")
            else:
                logger.error(f"Gemini extract_intent error: {ex}")
            return self.keyword_fallback(user_message, user_state)

def get_llm_provider() -> LLMProvider:
    return GeminiService()

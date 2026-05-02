# WhatsApp HotelBot

A production-ready WhatsApp hotel booking chatbot built with FastAPI, Meta Cloud API, Google Gemini, and Firebase.

## Features
- **End-to-End Booking:** Seamlessly handles city, dates, and hotel selection.
- **Interactive UI:** Utilizes WhatsApp native list messages for selecting cities and hotels.
- **PDF Receipts:** Automatically generates and sends branded booking invoices directly in chat.
- **Admin Dashboard:** Built-in web dashboard at `/dashboard` to view bookings and revenue.
- **Robust Fallback:** Uses AI-driven intent extraction with a reliable regex fallback mechanism for high availability.

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set your environment variables (Firebase, Meta API, Gemini)
4. Run the server: `uvicorn main:app --reload`

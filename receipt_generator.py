import os
from fpdf import FPDF
from datetime import datetime

class PDFReceipt(FPDF):
    def header(self):
        # Logo / Branding
        self.set_font('Arial', 'B', 24)
        self.set_text_color(79, 70, 229) # Indigo 600
        self.cell(0, 15, 'HotelBot Booking Receipt', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'Your seamless travel companion across India', 0, 1, 'C')
        self.ln(5)
        
        # Line break
        self.set_line_width(0.5)
        self.line(10, 35, 200, 35)
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.line(10, 275, 200, 275)
        self.cell(0, 10, 'Thank you for booking with HotelBot! For support, contact Vansh Gehlot.', 0, 1, 'C')
        self.cell(0, 5, 'Page ' + str(self.page_no()), 0, 0, 'C')

def generate_receipt(booking_data: dict, filepath: str):
    """
    Generates a PDF receipt and saves it to the given filepath.
    booking_data expects:
    - booking_id
    - guest_name
    - guest_email
    - phone
    - hotel_name
    - city
    - checkin
    - checkout
    - nights
    - rooms
    - price_per_night
    - total_price
    - created_at
    """
    pdf = PDFReceipt()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, 'BOOKING CONFIRMATION', 0, 1, 'L')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Booking ID: {booking_data.get('booking_id')}", 0, 1, 'L')
    pdf.cell(0, 8, f"Date: {booking_data.get('created_at', datetime.utcnow().isoformat())[:10]}", 0, 1, 'L')
    pdf.ln(10)
    
    # Guest Details
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(243, 244, 246) # Gray 100
    pdf.cell(0, 10, ' Guest Details ', 0, 1, 'L', fill=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(50, 8, 'Name:', 0, 0)
    pdf.cell(0, 8, str(booking_data.get('guest_name', 'N/A')), 0, 1)
    pdf.cell(50, 8, 'Email:', 0, 0)
    pdf.cell(0, 8, str(booking_data.get('guest_email', 'N/A')), 0, 1)
    pdf.cell(50, 8, 'Phone:', 0, 0)
    pdf.cell(0, 8, str(booking_data.get('phone', 'N/A')), 0, 1)
    pdf.ln(5)

    # Hotel Details
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, ' Stay Details ', 0, 1, 'L', fill=True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(50, 8, 'Hotel:', 0, 0)
    pdf.cell(0, 8, str(booking_data.get('hotel_name', 'N/A')), 0, 1)
    pdf.cell(50, 8, 'City:', 0, 0)
    pdf.cell(0, 8, str(booking_data.get('city', 'N/A')), 0, 1)
    pdf.cell(50, 8, 'Check-in:', 0, 0)
    pdf.cell(0, 8, str(booking_data.get('checkin', 'N/A')), 0, 1)
    pdf.cell(50, 8, 'Check-out:', 0, 0)
    pdf.cell(0, 8, str(booking_data.get('checkout', 'N/A')), 0, 1)
    pdf.cell(50, 8, 'Rooms:', 0, 0)
    pdf.cell(0, 8, str(booking_data.get('rooms', 1)), 0, 1)
    pdf.cell(50, 8, 'Nights:', 0, 0)
    pdf.cell(0, 8, str(booking_data.get('nights', 1)), 0, 1)
    pdf.ln(5)
    
    # Payment Summary
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, ' Payment Summary ', 0, 1, 'L', fill=True)
    pdf.set_font('Arial', '', 12)
    
    ppn = booking_data.get('price_per_night', 0)
    total = booking_data.get('total_price', 0)
    
    pdf.cell(100, 8, 'Price per night:', 0, 0)
    pdf.cell(0, 8, f"INR {ppn:,.2f}", 0, 1, 'R')
    pdf.set_line_width(0.2)
    pdf.line(10, pdf.get_y()+2, 200, pdf.get_y()+2)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(16, 185, 129) # Green
    pdf.cell(100, 10, 'Total Paid:', 0, 0)
    pdf.cell(0, 10, f"INR {total:,.2f}", 0, 1, 'R')
    
    # Save PDF
    pdf.output(filepath)
    return filepath

def process_and_send_receipt(phone: str, booking_data: dict):
    import tempfile
    import os
    from app.services.whatsapp import whatsapp_service
    
    try:
        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        
        # Generate PDF
        generate_receipt(booking_data, temp_path)
        
        # Upload to WhatsApp
        media_id = whatsapp_service.upload_media(temp_path)
        
        if media_id:
            whatsapp_service.send_document_message(
                phone=phone,
                media_id=media_id,
                filename=f"Booking_Receipt_{booking_data.get('booking_id', 'XXX')}.pdf"
            )
            
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    except Exception as e:
        print(f"Error processing receipt: {e}")

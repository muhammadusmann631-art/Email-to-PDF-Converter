import imaplib
import email
from email.header import decode_header
import os
import time
from datetime import datetime
from fpdf import FPDF

# ============== YOUR CONFIGURATION ==============
EMAIL = "muhammadusmnn631@gmail.com"
PASSWORD = "witrbmzgvboacnjh"  # ← APNA 16 DIGIT APP PASSWORD YAHAN DAALO
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
CHECK_INTERVAL = 60  # Har 60 second mein check karega
SAVE_FOLDER = "email_pdfs"

# Create folder if not exists
os.makedirs(SAVE_FOLDER, exist_ok=True)


def decode_email_subject(subject):
    """Decode email subject from various encodings"""
    decoded_parts = decode_header(subject)
    subject_text = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            subject_text += part.decode(encoding or 'utf-8', errors='replace')
        else:
            subject_text += part
    return subject_text.strip()


def get_email_body(msg):
    """Extract email body (text and html)"""
    body = ""
    html_body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                except:
                    pass
            elif content_type == "text/html" and "attachment" not in content_disposition:
                try:
                    html_body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
        except:
            pass
    
    return body or html_body or "No content"


def sanitize_filename(text, max_length=50):
    """Create safe filename from text"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        text = text.replace(char, '_')
    text = text[:max_length].strip()
    return text if text else "untitled"


def create_pdf(email_data, save_path):
    """Create PDF from email data"""
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, 'Email', ln=True)
    
    # Subject
    pdf.set_font('Helvetica', 'B', 14)
    pdf.multi_cell(0, 8, f"Subject: {email_data['subject']}")
    pdf.ln(2)
    
    # Sender
    pdf.set_font('Helvetica', '', 12)
    pdf.multi_cell(0, 6, f"From: {email_data['sender']}")
    pdf.multi_cell(0, 6, f"Date: {email_data['date']}")
    pdf.ln(5)
    
    # Separator line
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Body
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 6, email_data['body'][:2000])
    
    # Footer
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.cell(0, 5, f"Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    
    pdf.output(save_path)


def connect_to_email():
    """Connect to Gmail"""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL, PASSWORD)
        return mail
    except Exception as e:
        print(f"Connection error: {e}")
        return None


def check_new_emails():
    """Check for new emails and save as PDF"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking emails...")
    
    mail = connect_to_email()
    if not mail:
        return
    
    try:
        mail.select("inbox")
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        
        processed_file = os.path.join(SAVE_FOLDER, "processed_ids.txt")
        processed_ids = set()
        
        if os.path.exists(processed_file):
            with open(processed_file, 'r') as f:
                processed_ids = set(line.strip() for line in f)
        
        new_count = 0
        
        for email_id in email_ids:
            email_id_str = email_id.decode('utf-8')
            
            if email_id_str in processed_ids:
                continue
            
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = decode_email_subject(msg["Subject"] or "No Subject")
            sender = email.utils.parseaddr(msg["From"])[1] or msg["From"]
            date = msg["Date"] or datetime.now().isoformat()
            body = get_email_body(msg)
            
            email_data = {
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body
            }
            
            safe_subject = sanitize_filename(subject)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"email_{timestamp}_{safe_subject}.pdf"
            pdf_path = os.path.join(SAVE_FOLDER, pdf_filename)
            
            create_pdf(email_data, pdf_path)
            print(f"  ✓ Saved: {pdf_filename}")
            
            processed_ids.add(email_id_str)
            new_count += 1
        
        with open(processed_file, 'w') as f:
            f.write('\n'.join(processed_ids))
        
        if new_count > 0:
            print(f"  → {new_count} new email(s) saved!")
        
        mail.logout()
        
    except Exception as e:
        print(f"Error checking emails: {e}")


def run_agent():
    """Run the email agent continuously"""
    print("=" * 50)
    print("📧 EMAIL TO PDF AGENT")
    print("=" * 50)
    print(f"Monitoring: {EMAIL}")
    print(f"Save folder: {os.path.abspath(SAVE_FOLDER)}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("=" * 50)
    print("Press Ctrl+C to stop\n")
    
    check_new_emails()
    
    while True:
        time.sleep(CHECK_INTERVAL)
        check_new_emails()


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║           📧 EMAIL TO PDF AUTOMATIC AGENT 📧              ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    response = input("Have you completed the setup? (yes/no): ")
    
    if response.lower() == 'yes':
        run_agent()
    else:
        print("Please complete the setup steps first, then run the script again.")

"""
send_report.py
==============

Sends the generated AI Traffic PDF report securely via email
using Gmail's SMTP server. Masks the password in the terminal.
"""

import smtplib
import ssl
from email.message import EmailMessage
import getpass
import os
from dotenv import load_dotenv

def dispatch_email(target_receiver_email=None):
    # Setup Paths
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    
    # Load environment variables from specific .env file
    env_path = os.path.join(PROJECT_ROOT, "app", "config", "env", ".env")
    load_dotenv(dotenv_path=env_path)

    PDF_PATH = os.path.join(PROJECT_ROOT, "reports", "exports", "traffic.pdf")
    
    print("\n=== AI Traffic Email Dispatcher ===")
    
    # 1. Verify existence of the PDF before taking inputs
    if not os.path.exists(PDF_PATH):
        print(f"[ERROR] Could not find PDF at: {PDF_PATH}")
        print("Please ensure you have run 6_report.py successfully first.")
        raise FileNotFoundError("PDF report not found. Generate it first.")

    # 2. Get securely prompted credentials with fallback
    env_sender = os.getenv("SENDER_EMAIL")
    sender_email = env_sender if env_sender else os.getenv("EMAIL_USER")
    
    env_password = os.getenv("APP_PASSWORD")
    app_password = env_password if env_password else os.getenv("EMAIL_PASS")
    
    if not sender_email or not app_password:
        raise ValueError("Missing SENDER_EMAIL or APP_PASSWORD in .env")
        
    receiver_email = target_receiver_email if target_receiver_email else os.getenv("RECEIVER_EMAIL")
    if not receiver_email:
        raise ValueError("No receiver email specified.")
    
    # 3. Format the Email Core
    msg = EmailMessage()
    msg['Subject'] = "Traffic Analysis Report"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    # Email Body Content
    msg.set_content("Hello,\n\nYour traffic analysis report is attached.\n\nBest,\nAutomated AI System")

    # 4. Read physical PDF into memory and attach it
    try:
        with open(PDF_PATH, 'rb') as f:
            pdf_data = f.read()
            pdf_filename = os.path.basename(PDF_PATH)
            
        msg.add_attachment(
            pdf_data, 
            maintype='application', 
            subtype='pdf', 
            filename=pdf_filename
        )
    except Exception as e:
        print(f"[ERROR] Failed to attach the physical PDF file: {e}")
        return

    # 5. Connect securely using SSL configuration (Port 465)
    print("\n[INFO] Contacting Gmail Servers...")
    context = ssl.create_default_context()
    
    try:
        # Open secure channel
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            # Login authentication
            server.login(sender_email, app_password)
            # Send packaged email
            server.send_message(msg)
            
            print("[SUCCESS] Traffic report email successfully sent!")
            
    except smtplib.SMTPAuthenticationError:
        print("\n[ERROR] Login failed! Incorrect email or password.")
        print("Note: You MUST use an 'App Password', not your standard Google Login password.")
    except Exception as e:
        print(f"\n[ERROR] An unexpected network error occurred: {e}")

if __name__ == "__main__":
    dispatch_email()

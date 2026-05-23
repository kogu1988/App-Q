from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

def send_report_email(to_address: str, study_title: str, summary_text: str, pdf_bytes: bytes) -> bool:
    """
    Sends an email with the PDF report attached.
    Reads SMTP config from environment variables.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    
    if not smtp_user or not smtp_pass:
        raise ValueError("SMTP_USER or SMTP_PASS environment variables are not set.")

    msg = EmailMessage()
    msg["Subject"] = f"App-Q Araştırma Raporu: {study_title}"
    msg["From"] = smtp_user
    msg["To"] = to_address
    
    body = f"""Merhaba,

"{study_title}" başlıklı pazar araştırması raporunuz başarıyla oluşturuldu.
Raporun PDF sürümünü ekte bulabilirsiniz.

Yönetici Özeti:
{summary_text}

İyi çalışmalar,
App-Q Sistemi
"""
    msg.set_content(body)
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=f"App-Q_Report_{study_title.replace(' ', '_')}.pdf")

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise e

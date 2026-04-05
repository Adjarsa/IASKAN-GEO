"""
Contact Router - Contact Form Handling
Migrated from server.py for better code organization
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
import os
import logging

router = APIRouter(prefix="/api", tags=["contact"])
logger = logging.getLogger(__name__)

# Email Configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')


class ContactForm(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    subject: str
    message: str


@router.post("/contact")
async def send_contact_message(form: ContactForm):
    """Handle contact form submission - PostgreSQL version"""
    try:
        from ..db.database import async_session_maker
        from ..db.models import ContactMessage
        
        async with async_session_maker() as session:
            contact = ContactMessage(
                contact_id=f"contact_{uuid.uuid4().hex[:12]}",
                name=form.name,
                email=form.email,
                company=form.company,
                subject=form.subject,
                message=form.message,
                status="new"
            )
            session.add(contact)
            await session.commit()
        
        # Send notification email to admin
        if RESEND_API_KEY:
            import resend
            resend.api_key = RESEND_API_KEY
            
            subject_labels = {
                "demo": "Demande de démo",
                "pricing": "Question tarifs",
                "support": "Support technique",
                "partnership": "Partenariat",
                "other": "Autre"
            }
            subject_label = subject_labels.get(form.subject, form.subject)
            
            try:
                params = {
                    "from": "IAskan Contact <noreply@resend.dev>",
                    "to": ["contact@iaskan.com"],
                    "reply_to": form.email,
                    "subject": f"[IAskan Contact] {subject_label} - {form.name}",
                    "html": f"""
                    <h2>Nouveau message de contact</h2>
                    <p><strong>Nom:</strong> {form.name}</p>
                    <p><strong>Email:</strong> {form.email}</p>
                    <p><strong>Entreprise:</strong> {form.company or 'Non renseigné'}</p>
                    <p><strong>Sujet:</strong> {subject_label}</p>
                    <hr/>
                    <p><strong>Message:</strong></p>
                    <p>{form.message}</p>
                    """
                }
                resend.Emails.send(params)
                logger.info(f"Contact email sent for {form.email}")
            except Exception as e:
                logger.error(f"Failed to send contact email: {e}")
        
        return {
            "success": True,
            "message": "Votre message a été envoyé avec succès. Nous vous répondrons dans les plus brefs délais."
        }
        
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi du message")

"""
Email Service
Handles all email communications via Resend
"""
import resend
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..core.config import RESEND_API_KEY, SENDER_EMAIL, FRONTEND_URL

logger = logging.getLogger(__name__)

# Initialize Resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY


# Email templates
def get_welcome_email_html(user_name: str) -> str:
    """Welcome email template"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenue sur IAskan</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <tr>
            <td style="background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%); padding: 40px 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 700;">IAskan</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">Generative Engine Optimization</p>
            </td>
        </tr>
        
        <!-- Content -->
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="color: #1e293b; margin: 0 0 20px 0; font-size: 24px;">
                    Bienvenue {user_name} ! 🎉
                </h2>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    Vous venez de rejoindre IAskan, la première plateforme de <strong>Generative Engine Optimization (GEO)</strong> en France.
                </p>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                    Avec IAskan, vous pouvez :
                </p>
                
                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                    <tr>
                        <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px; margin-bottom: 10px;">
                            <table cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="width: 40px; vertical-align: top;">
                                        <span style="font-size: 24px;">📊</span>
                                    </td>
                                    <td style="color: #475569; font-size: 14px;">
                                        <strong style="color: #1e293b;">Analyser votre visibilité IA</strong><br>
                                        Découvrez comment ChatGPT, Claude, Gemini et Perplexity parlent de votre marque
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr><td style="height: 10px;"></td></tr>
                    <tr>
                        <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px;">
                            <table cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="width: 40px; vertical-align: top;">
                                        <span style="font-size: 24px;">🎯</span>
                                    </td>
                                    <td style="color: #475569; font-size: 14px;">
                                        <strong style="color: #1e293b;">Obtenir des recommandations</strong><br>
                                        Recevez un plan d'action concret pour améliorer votre présence
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr><td style="height: 10px;"></td></tr>
                    <tr>
                        <td style="padding: 15px; background-color: #f8fafc; border-radius: 8px;">
                            <table cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="width: 40px; vertical-align: top;">
                                        <span style="font-size: 24px;">✨</span>
                                    </td>
                                    <td style="color: #475569; font-size: 14px;">
                                        <strong style="color: #1e293b;">Optimiser vos contenus</strong><br>
                                        Améliorez la citabilité de vos articles pour être recommandé par les IA
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
                
                <!-- CTA Button -->
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td align="center" style="padding: 10px 0 30px 0;">
                            <a href="{FRONTEND_URL}/projects" 
                               style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%); color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 8px;">
                                Commencer maintenant →
                            </a>
                        </td>
                    </tr>
                </table>
                
                <p style="color: #475569; font-size: 14px; line-height: 1.6; margin: 0; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                    <strong>Votre essai gratuit inclut :</strong><br>
                    • 1 scan GEO complet<br>
                    • 30 requêtes analysées sur ChatGPT<br>
                    • Rapport détaillé avec recommandations
                </p>
            </td>
        </tr>
        
        <!-- Footer -->
        <tr>
            <td style="background-color: #1e293b; padding: 30px; text-align: center;">
                <p style="color: #94a3b8; font-size: 12px; margin: 0 0 10px 0;">
                    © 2026 IAskan - Tous droits réservés
                </p>
                <p style="color: #64748b; font-size: 11px; margin: 0;">
                    <a href="{FRONTEND_URL}/unsubscribe" style="color: #64748b;">Se désinscrire</a> · 
                    <a href="{FRONTEND_URL}/privacy" style="color: #64748b;">Politique de confidentialité</a>
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_scan_complete_email_html(
    user_name: str,
    project_name: str,
    brand_name: str,
    global_score: float,
    grade: str,
    analysis_id: str,
    top_recommendations: list = None
) -> str:
    """Scan completion email template"""
    
    # Grade color
    grade_colors = {
        'A': '#10b981',
        'B': '#22c55e', 
        'C': '#eab308',
        'D': '#f97316',
        'F': '#ef4444'
    }
    grade_color = grade_colors.get(grade, '#94a3b8')
    
    # Score color
    if global_score >= 70:
        score_color = '#10b981'
        score_text = 'Excellent'
    elif global_score >= 50:
        score_color = '#eab308'
        score_text = 'À améliorer'
    else:
        score_color = '#ef4444'
        score_text = 'Nécessite attention'
    
    # Recommendations HTML
    recommendations_html = ""
    if top_recommendations:
        recommendations_html = """
        <tr>
            <td style="padding: 20px 0;">
                <h3 style="color: #1e293b; font-size: 16px; margin: 0 0 15px 0;">Top recommandations :</h3>
        """
        for i, rec in enumerate(top_recommendations[:3], 1):
            recommendations_html += f"""
                <p style="color: #475569; font-size: 14px; line-height: 1.5; margin: 0 0 10px 0; padding-left: 20px;">
                    <span style="color: #8b5cf6; font-weight: 600;">{i}.</span> {rec}
                </p>
            """
        recommendations_html += """
            </td>
        </tr>
        """
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Votre analyse GEO est prête</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <tr>
            <td style="background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%); padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">IAskan</h1>
            </td>
        </tr>
        
        <!-- Content -->
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="color: #1e293b; margin: 0 0 10px 0; font-size: 22px;">
                    Votre analyse GEO est prête ! 🎉
                </h2>
                
                <p style="color: #64748b; font-size: 14px; margin: 0 0 30px 0;">
                    Projet : <strong style="color: #1e293b;">{project_name}</strong> · Marque : <strong style="color: #1e293b;">{brand_name}</strong>
                </p>
                
                <!-- Score Card -->
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; border-radius: 12px; overflow: hidden; margin-bottom: 30px;">
                    <tr>
                        <td style="padding: 30px; text-align: center;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td width="50%" style="text-align: center; border-right: 1px solid #e2e8f0;">
                                        <p style="color: #64748b; font-size: 12px; text-transform: uppercase; margin: 0 0 10px 0;">Score GEO Global</p>
                                        <p style="color: {score_color}; font-size: 48px; font-weight: 700; margin: 0; line-height: 1;">{int(global_score)}</p>
                                        <p style="color: {score_color}; font-size: 14px; margin: 5px 0 0 0;">{score_text}</p>
                                    </td>
                                    <td width="50%" style="text-align: center;">
                                        <p style="color: #64748b; font-size: 12px; text-transform: uppercase; margin: 0 0 10px 0;">Note</p>
                                        <p style="color: {grade_color}; font-size: 48px; font-weight: 700; margin: 0; line-height: 1;">{grade}</p>
                                        <p style="color: #64748b; font-size: 14px; margin: 5px 0 0 0;">sur 4 IA</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
                
                {recommendations_html}
                
                <!-- CTA Button -->
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td align="center" style="padding: 10px 0;">
                            <a href="{FRONTEND_URL}/analysis/{analysis_id}" 
                               style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%); color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 8px;">
                                Voir le rapport complet →
                            </a>
                        </td>
                    </tr>
                </table>
                
                <p style="color: #64748b; font-size: 13px; text-align: center; margin: 30px 0 0 0;">
                    Cet email a été envoyé car vous avez lancé une analyse sur IAskan.
                </p>
            </td>
        </tr>
        
        <!-- Footer -->
        <tr>
            <td style="background-color: #1e293b; padding: 20px; text-align: center;">
                <p style="color: #64748b; font-size: 11px; margin: 0;">
                    <a href="{FRONTEND_URL}/settings" style="color: #64748b;">Gérer les notifications</a> · 
                    <a href="{FRONTEND_URL}/unsubscribe" style="color: #64748b;">Se désinscrire</a>
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_subscription_cancelled_email_html(
    user_name: str,
    plan_name: str,
    end_date: str
) -> str:
    """Subscription cancellation email template"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Confirmation de désabonnement</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <tr>
            <td style="background: linear-gradient(135deg, #64748b 0%, #475569 100%); padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">IAskan</h1>
            </td>
        </tr>
        
        <!-- Content -->
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="color: #1e293b; margin: 0 0 20px 0; font-size: 22px;">
                    Votre désabonnement est confirmé
                </h2>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    Bonjour {user_name},
                </p>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    Nous confirmons l'annulation de votre abonnement <strong>{plan_name}</strong>.
                </p>
                
                <!-- Info Box -->
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fef3c7; border-radius: 8px; margin-bottom: 30px;">
                    <tr>
                        <td style="padding: 20px;">
                            <p style="color: #92400e; font-size: 14px; margin: 0;">
                                <strong>Important :</strong> Vous conservez l'accès à toutes les fonctionnalités jusqu'au <strong>{end_date}</strong>.
                            </p>
                        </td>
                    </tr>
                </table>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                    Après cette date, votre compte passera automatiquement au plan gratuit. Vos projets et historiques d'analyses seront conservés.
                </p>
                
                <h3 style="color: #1e293b; font-size: 16px; margin: 0 0 15px 0;">Ce qui nous manquera :</h3>
                
                <ul style="color: #475569; font-size: 14px; line-height: 1.8; margin: 0 0 30px 0; padding-left: 20px;">
                    <li>Vos analyses GEO régulières</li>
                    <li>Votre progression dans l'optimisation IA</li>
                    <li>Nos échanges sur vos recommandations</li>
                </ul>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                    Si vous changez d'avis, vous pouvez vous réabonner à tout moment :
                </p>
                
                <!-- CTA Button -->
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td align="center">
                            <a href="{FRONTEND_URL}/pricing" 
                               style="display: inline-block; padding: 14px 30px; background-color: #8b5cf6; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 14px; border-radius: 8px;">
                                Voir les offres
                            </a>
                        </td>
                    </tr>
                </table>
                
                <p style="color: #64748b; font-size: 14px; margin: 30px 0 0 0; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                    Vous avez une question ou un feedback ? Répondez simplement à cet email, nous serons ravis de vous lire.
                </p>
            </td>
        </tr>
        
        <!-- Footer -->
        <tr>
            <td style="background-color: #1e293b; padding: 20px; text-align: center;">
                <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                    Merci d'avoir utilisé IAskan 💜
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def get_subscription_reminder_email_html(
    user_name: str,
    plan_name: str,
    days_remaining: int
) -> str:
    """Subscription expiration reminder email"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Votre abonnement expire bientôt</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <tr>
            <td style="background: linear-gradient(135deg, #f97316 0%, #eab308 100%); padding: 30px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">IAskan</h1>
            </td>
        </tr>
        
        <!-- Content -->
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="color: #1e293b; margin: 0 0 20px 0; font-size: 22px;">
                    ⏰ Votre abonnement expire dans {days_remaining} jour{"s" if days_remaining > 1 else ""}
                </h2>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                    Bonjour {user_name},
                </p>
                
                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                    Votre abonnement <strong>{plan_name}</strong> arrive à expiration. Pour continuer à bénéficier de toutes les fonctionnalités, pensez à renouveler votre abonnement.
                </p>
                
                <!-- Warning Box -->
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fef2f2; border-radius: 8px; border-left: 4px solid #ef4444; margin-bottom: 30px;">
                    <tr>
                        <td style="padding: 20px;">
                            <p style="color: #991b1b; font-size: 14px; margin: 0;">
                                <strong>Sans renouvellement :</strong><br>
                                • Vos scans programmés seront désactivés<br>
                                • L'optimiseur d'articles sera limité<br>
                                • Le benchmark concurrents ne sera plus disponible
                            </p>
                        </td>
                    </tr>
                </table>
                
                <!-- CTA Button -->
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td align="center">
                            <a href="{FRONTEND_URL}/settings" 
                               style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%); color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 8px;">
                                Renouveler maintenant →
                            </a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        
        <!-- Footer -->
        <tr>
            <td style="background-color: #1e293b; padding: 20px; text-align: center;">
                <p style="color: #64748b; font-size: 11px; margin: 0;">
                    <a href="{FRONTEND_URL}/settings" style="color: #64748b;">Gérer mon abonnement</a> · 
                    <a href="{FRONTEND_URL}/unsubscribe" style="color: #64748b;">Se désinscrire</a>
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
"""


class EmailService:
    """Service for sending transactional emails"""
    
    @staticmethod
    async def send_welcome_email(email: str, user_name: str) -> bool:
        """Send welcome email to new user"""
        if not RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return False
        
        try:
            html_content = get_welcome_email_html(user_name)
            
            resend.Emails.send({
                "from": f"IAskan <{SENDER_EMAIL}>",
                "to": [email],
                "subject": f"Bienvenue sur IAskan, {user_name} ! 🚀",
                "html": html_content
            })
            
            logger.info(f"Welcome email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {e}")
            return False
    
    @staticmethod
    async def send_scan_complete_email(
        email: str,
        user_name: str,
        project_name: str,
        brand_name: str,
        global_score: float,
        grade: str,
        analysis_id: str,
        recommendations: list = None
    ) -> bool:
        """Send scan completion notification email"""
        if not RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return False
        
        try:
            html_content = get_scan_complete_email_html(
                user_name=user_name,
                project_name=project_name,
                brand_name=brand_name,
                global_score=global_score,
                grade=grade,
                analysis_id=analysis_id,
                top_recommendations=recommendations
            )
            
            # Emoji based on grade
            emoji = "🎉" if grade in ['A', 'B'] else "📊" if grade == 'C' else "⚠️"
            
            resend.Emails.send({
                "from": f"IAskan <{SENDER_EMAIL}>",
                "to": [email],
                "subject": f"{emoji} Votre analyse GEO est prête - Score: {int(global_score)}/100",
                "html": html_content
            })
            
            logger.info(f"Scan complete email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send scan complete email to {email}: {e}")
            return False
    
    @staticmethod
    async def send_subscription_cancelled_email(
        email: str,
        user_name: str,
        plan_name: str,
        end_date: str
    ) -> bool:
        """Send subscription cancellation confirmation email"""
        if not RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return False
        
        try:
            html_content = get_subscription_cancelled_email_html(
                user_name=user_name,
                plan_name=plan_name,
                end_date=end_date
            )
            
            resend.Emails.send({
                "from": f"IAskan <{SENDER_EMAIL}>",
                "to": [email],
                "subject": "Confirmation de désabonnement - IAskan",
                "html": html_content
            })
            
            logger.info(f"Subscription cancelled email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send subscription cancelled email to {email}: {e}")
            return False
    
    @staticmethod
    async def send_subscription_reminder_email(
        email: str,
        user_name: str,
        plan_name: str,
        days_remaining: int
    ) -> bool:
        """Send subscription expiration reminder email"""
        if not RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not configured, skipping email")
            return False
        
        try:
            html_content = get_subscription_reminder_email_html(
                user_name=user_name,
                plan_name=plan_name,
                days_remaining=days_remaining
            )
            
            resend.Emails.send({
                "from": f"IAskan <{SENDER_EMAIL}>",
                "to": [email],
                "subject": f"⏰ Votre abonnement IAskan expire dans {days_remaining} jour{'s' if days_remaining > 1 else ''}",
                "html": html_content
            })
            
            logger.info(f"Subscription reminder email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send subscription reminder email to {email}: {e}")
            return False


# Singleton instance
email_service = EmailService()

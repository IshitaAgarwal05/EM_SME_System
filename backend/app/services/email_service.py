"""
Email service for sending transactional emails.
Uses Resend API for reliable email delivery.
"""

import os
from typing import Optional

import structlog
import resend

from app.config import settings

logger = structlog.get_logger()


class EmailService:
    """Service for sending emails via Resend."""

    def __init__(self):
        # Configure resend with API key (new v2.x API)
        if settings.resend_api_key:
            resend.api_key = settings.resend_api_key
            self.is_configured = True
        else:
            self.is_configured = False
        self.from_email = settings.from_email
        self.frontend_url = settings.frontend_url

    async def send_invitation_email(
        self,
        to_email: str,
        inviter_name: str,
        organization_name: str,
        invite_token: str,
        role: str,
    ) -> bool:
        """
        Send team invitation email with magic link.
        
        Args:
            to_email: Recipient email address
            inviter_name: Name of person who sent invitation
            organization_name: Name of the organization
            invite_token: Unique invitation token
            role: Role being invited to (manager, employee, contractor)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning("resend_not_configured", action="skipping_email")
            return False

        invite_url = f"{self.frontend_url}/accept-invite/{invite_token}"

        subject = f"{inviter_name} invited you to join {organization_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Team Invitation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">You're Invited!</h1>
            </div>
            
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p style="font-size: 16px; margin-bottom: 20px;">
                    <strong>{inviter_name}</strong> has invited you to join <strong>{organization_name}</strong> as a <strong>{role}</strong>.
                </p>
                
                <p style="margin-bottom: 30px;">
                    Click the button below to accept the invitation and create your account:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invite_url}" 
                       style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; 
                              padding: 15px 40px; 
                              text-decoration: none; 
                              border-radius: 5px; 
                              font-weight: bold;
                              display: inline-block;">
                        Accept Invitation
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    Or copy and paste this link into your browser:
                </p>
                <p style="font-size: 12px; color: #667eea; word-break: break-all;">
                    {invite_url}
                </p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    This invitation will expire in 7 days.<br>
                    If you didn't expect this invitation, you can safely ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

        try:
            params: resend.Emails.SendParams = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            response = resend.Emails.send(params)
            
            logger.info(
                "invitation_email_sent",
                to_email=to_email,
                organization=organization_name,
                email_id=getattr(response, 'id', None),
            )
            return True
            
        except Exception as e:
            logger.error(
                "invitation_email_failed",
                to_email=to_email,
                error=str(e),
            )
            return False

    async def send_welcome_email(
        self,
        to_email: str,
        full_name: str,
        organization_name: str,
    ) -> bool:
        """Send welcome email to new team member."""
        if not self.is_configured:
            return False

        subject = f"Welcome to {organization_name}!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #667eea;">Welcome to {organization_name}, {full_name}!</h2>
            
            <p>Your account has been successfully created. You can now:</p>
            
            <ul>
                <li>Manage tasks and projects</li>
                <li>Track financial transactions</li>
                <li>Collaborate with your team</li>
                <li>Access AI-powered insights</li>
            </ul>
            
            <p>
                <a href="{self.frontend_url}/login" 
                   style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Go to Dashboard
                </a>
            </p>
            
            <p style="margin-top: 30px; font-size: 14px; color: #666;">
                Need help? Contact your team manager or check out our documentation.
            </p>
        </body>
        </html>
        """

        try:
            params: resend.Emails.SendParams = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            resend.Emails.send(params)
            return True
        except Exception as e:
            logger.error("welcome_email_failed", to_email=to_email, error=str(e))
            return False

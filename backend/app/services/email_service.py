import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from dotenv import load_dotenv
from mailgun.client import Client

load_dotenv()

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        # Mailgun API configuration
        self.mailgun_api_key = os.getenv("MAILGUN_API_KEY")
        self.mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        self.mailgun_client = None
        if self.mailgun_api_key:
            self.mailgun_client = Client(api_key=self.mailgun_api_key, region='US')
        
        # SMTP configuration
        self.smtp_server = os.getenv("MAIL_SERVER")
        self.smtp_port = int(os.getenv("MAIL_PORT", "587"))
        self.smtp_use_tls = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
        self.smtp_username = os.getenv("MAIL_USERNAME")
        self.smtp_password = os.getenv("MAIL_PASSWORD")
        
        # Sender configuration
        self.from_email = os.getenv("MAIL_FROM_EMAIL", "noreply@annie-defect.com")
        self.from_name = os.getenv("MAIL_FROM_NAME", "Annie Defect Tracking")
        
        # Determine which email method to use
        self.use_mailgun = bool(self.mailgun_api_key and self.mailgun_domain)
        self.use_smtp = bool(self.smtp_server and self.smtp_username and self.smtp_password)
        
        if not self.use_mailgun and not self.use_smtp:
            logger.warning("No email configuration found. Emails will be logged only.")
    
    async def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email using configured method (Mailgun API or SMTP)."""
        try:
            if self.use_mailgun:
                return await self._send_via_mailgun(to_email, subject, body, html_body)
            elif self.use_smtp:
                return await self._send_via_smtp(to_email, subject, body, html_body)
            else:
                logger.info(f"Email (no sender configured) - To: {to_email}, Subject: {subject}")
                logger.info(f"Body: {body}")
                return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    async def _send_via_mailgun(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email using Mailgun API."""
        try:
            import requests
            
            data = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": to_email,
                "subject": subject,
                "text": body
            }
            
            if html_body:
                data["html"] = html_body
            
            # Send using requests directly
            response = requests.post(
                f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages",
                auth=("api", self.mailgun_api_key),
                data=data
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully via Mailgun to {to_email}")
                return True
            else:
                logger.error(f"Mailgun API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Mailgun send error: {str(e)}")
            return False
    
    async def _send_via_smtp(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email using SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully via SMTP to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP send error: {str(e)}")
            return False
    
    async def send_password_reset_code(self, email: str, code: str) -> bool:
        """Send password reset code email."""
        subject = "Your Password Reset Code - Annie Defect Tracking"
        
        body = f"""Hello,

You requested a password reset for your Annie Defect Tracking account.

Your password reset code is: {code}

This code will expire in 15 minutes.

If you didn't request this password reset, please ignore this email.

Best regards,
Annie Defect Tracking Team"""
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2196F3;">Password Reset Request</h2>
                    <p>Hello,</p>
                    <p>You requested a password reset for your Annie Defect Tracking account.</p>
                    <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0; text-align: center; border-radius: 5px;">
                        <p style="margin: 0; font-size: 14px; color: #666;">Your password reset code is:</p>
                        <h1 style="margin: 10px 0; color: #2196F3; letter-spacing: 5px;">{code}</h1>
                    </div>
                    <p><strong>This code will expire in 15 minutes.</strong></p>
                    <p style="color: #666; font-size: 14px;">If you didn't request this password reset, please ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #999; font-size: 12px;">Best regards,<br>Annie Defect Tracking Team</p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(email, subject, body, html_body)
    
    async def send_welcome_email(self, email: str, first_name: str) -> bool:
        """Send welcome email after registration."""
        subject = "Welcome to Annie Defect Tracking"
        
        body = f"""Hello {first_name},

Welcome to Annie Defect Tracking! Your account has been successfully created.

You can now log in using your email address and the password you created during registration.

If you have any questions or need assistance, please don't hesitate to contact our support team.

Best regards,
Annie Defect Tracking Team"""
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2196F3;">Welcome to Annie Defect Tracking!</h2>
                    <p>Hello {first_name},</p>
                    <p>Your account has been successfully created. You can now log in using your email address and the password you created during registration.</p>
                    <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #2196F3;">Getting Started</h3>
                        <ul style="color: #666;">
                            <li>Upload your Fulcrum data ZIP files</li>
                            <li>Let our AI analyze building defects</li>
                            <li>Generate detailed cost estimates</li>
                            <li>Export professional reports</li>
                        </ul>
                    </div>
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #999; font-size: 12px;">Best regards,<br>Annie Defect Tracking Team</p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(email, subject, body, html_body)
    
    async def send_defect_report_ready(self, email: str, first_name: str, project_name: str) -> bool:
        """Send notification when defect analysis is complete."""
        subject = f"Your Defect Report is Ready - {project_name}"
        
        body = f"""Hello {first_name},

Good news! The AI analysis for your project "{project_name}" has been completed.

Your defect report is now ready for download. You can access it by logging into your Annie Defect Tracking account.

The report includes:
- Detailed defect classifications
- AI-generated cost estimates
- Remediation recommendations
- Photo analysis results

Best regards,
Annie Defect Tracking Team"""
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2196F3;">Your Defect Report is Ready!</h2>
                    <p>Hello {first_name},</p>
                    <p>Good news! The AI analysis for your project <strong>"{project_name}"</strong> has been completed.</p>
                    <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px;">
                        <h3 style="margin-top: 0; color: #2196F3;">Report Includes:</h3>
                        <ul style="color: #666;">
                            <li>Detailed defect classifications</li>
                            <li>AI-generated cost estimates</li>
                            <li>Remediation recommendations</li>
                            <li>Photo analysis results</li>
                        </ul>
                    </div>
                    <p>
                        <a href="{os.getenv('FRONTEND_URL', 'http://localhost:5179')}/projects" 
                           style="display: inline-block; padding: 12px 30px; background-color: #2196F3; color: white; text-decoration: none; border-radius: 5px;">
                            View Your Report
                        </a>
                    </p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #999; font-size: 12px;">Best regards,<br>Annie Defect Tracking Team</p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(email, subject, body, html_body)
    
    async def send_account_deactivated(self, email: str, first_name: str) -> bool:
        """Send notification when account is deactivated."""
        subject = "Account Deactivated - Annie Defect Tracking"
        
        body = f"""Hello {first_name},

Your Annie Defect Tracking account has been deactivated by an administrator.

If you believe this is an error or would like to reactivate your account, please contact our support team.

Best regards,
Annie Defect Tracking Team"""
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #d32f2f;">Account Deactivated</h2>
                    <p>Hello {first_name},</p>
                    <p>Your Annie Defect Tracking account has been deactivated by an administrator.</p>
                    <p>If you believe this is an error or would like to reactivate your account, please contact our support team.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #999; font-size: 12px;">Best regards,<br>Annie Defect Tracking Team</p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(email, subject, body, html_body)


# Singleton instance
email_service = EmailService()
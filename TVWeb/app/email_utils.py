# -*- coding: utf-8 -*-

import os
import jwt
import datetime
from flask import current_app, flash, redirect
from flask_mail import Mail, Message

MAIL_SERVER='SMTP_SERVER'
MAIL_PORT=0
MAIL_USE_SSL=False
MAIL_USE_TLS=False
MAIL_USERNAME='SMTP_USERNAME'
MAIL_PASSWORD='SMTP_PASSWORD'
MAIL_DEFAULT_SENDER='FROM_EMAIL'
IMAP_SERVER='IMAP_SERVER'
IMAP_PORT=0

App=""
mail=""

# Flask-Mail Configuration
def init_mail(app):
    """
    Initialize Flask-Mail with SMTP parameters from environment variables
    """
    global App, mail, \
        MAIL_SERVER, MAIL_PORT, \
        MAIL_USE_SSL, MAIL_USE_TLS, \
        MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER, \
        IMAP_SERVER, IMAP_PORT

    
    # Read MAIL environment variables
    MAIL_SERVER=os.getenv('SMTP_SERVER')                    
    MAIL_PORT=int(os.getenv('SMTP_PORT'))                   
    MAIL_USE_SSL=os.getenv('SMTP_USE_SSL').lower() == 'true'
    MAIL_USE_TLS=os.getenv('SMTP_USE_TLS').lower() == 'true'
    MAIL_USERNAME=os.getenv('SMTP_USERNAME')                
    MAIL_PASSWORD=os.getenv('SMTP_PASSWORD')                
    MAIL_DEFAULT_SENDER=os.getenv('FROM_EMAIL')
    IMAP_SERVER=os.getenv('IMAP_SERVER')
    IMAP_PORT=int(os.getenv('IMAP_PORT'))

    app.config['MAIL_SERVER'] = MAIL_SERVER
    app.config['MAIL_PORT'] = MAIL_PORT
    app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
    app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
    app.config['MAIL_USERNAME'] = MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
    app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER
    App=app
    
    # Initialize Flask-Mail
    mail = Mail(app)
    return mail

# Global variable to store mail instance
mail_instance = None

def get_mail():
    """
    Return Flask-Mail instance
    """
    global mail
    
    if mail is None:
        # Throw an error
        flash("Error with SMTP mail server not configured.")
        return redirect(url_for("home"))
        
    return mail

# Token Generation and Verification Functions
def generate_verification_token(user_id, secret_key=None, expiration_sec=3600):
    """
    Generate a JWT token for email verification
    Args:
        user_id: The user's ID
        secret_key: Secret key for JWT signing (if None, will try to get from current_app)
        expiration_sec: Token expiration time in seconds (default: 1 hour)
    Returns:
        JWT token string
    """
    # Create expiration datetime (UTC)
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration_sec)
    
    # Package data to be tokenized
    data = {
        "exp": expiration_time,
        "confirm_id": user_id
    }
    
    # Get secret key
    if secret_key is None:
        try:
            secret_key = current_app.secret_key
        except RuntimeError:
            # Fallback if not in app context
            secret_key = os.getenv('SECRET_KEY', 'I-am-a-funny-unicorn')
    
    # Generate token using HS512 algorithm
    token = jwt.encode(data, secret_key, algorithm="HS512")
    return token

def verify_token(token, secret_key=None):
    """
    Verify and decode a JWT token
    Args:
        token: JWT token string
        secret_key: Secret key for JWT verification (if None, will try to get from current_app)
    Returns:
        dict with user_id if valid, None if invalid
    """
    try:
        # Get secret key
        if secret_key is None:
            try:
                secret_key = current_app.secret_key
            except RuntimeError:
                # Fallback if not in app context
                secret_key = os.getenv('SECRET_KEY', 'I-am-a-funny-unicorn')
        
        # Decode token and verify signature
        data = jwt.decode(token, secret_key, algorithms=["HS512"])
        return data
    except jwt.ExpiredSignatureError:
        # Token expired
        return None
    except jwt.InvalidSignatureError:
        # Invalid signature
        return None
    except jwt.InvalidTokenError:
        # Invalid token format
        return None

# Email Sending Functions
def send_verification_email(user_email, username, token):
    """
    Send verification email with JWT token
    Args:
        user_email: Recipient email address
        username: Username for personalization
        token: JWT verification token
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        from flask import current_app
        
        # Get SMTP configuration with fallback to hardcoded values
        smtp_server = MAIL_SERVER
        smtp_port = MAIL_PORT
        smtp_username = MAIL_USERNAME
        smtp_password = MAIL_PASSWORD
        from_email = MAIL_DEFAULT_SENDER
        
        # Create a fresh Mail instance
        from flask_mail import Mail
        mail = Mail(App)
        
        # Create verification URL
        server_name = os.getenv('SERVER_NAME')
        domain = os.getenv('DOMAIN')
        verification_url = f"https://{server_name}.{domain}/verify-email/{token}"
        
        # Create email message
        msg = Message(
            subject="TiledViz - Email Verification",
            recipients=[user_email],
            sender=from_email
        )
        
        # HTML content
        html_content = f"""
        <html>
        <body>
            <h2>Welcome to TiledViz, {username}!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email Address</a></p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{verification_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't create an account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>The TiledViz Team</p>
        </body>
        </html>
        """
        
        # Plain text content
        text_content = f"""
        Welcome to TiledViz, {username}!
        
        Thank you for registering. Please verify your email address by visiting the link below:
        
        {verification_url}
        
        This link will expire in 1 hour.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        The TiledViz Team
        """
        
        # Set both HTML and text content
        msg.html = html_content
        msg.body = text_content
        
        # Send email
        mail.send(msg)
        
        print(" Email sent successfully")
        return True
        
    except Exception as e:
        print(f" Error sending verification email: {e}")
        print(f" Error type: {type(e)}")
        import traceback
        print(f" Traceback: {traceback.format_exc()}")
        return False

# IMAP Functions for Email Management
def delete_sent_email(subject, recipient):
    """
    Delete sent email from IMAP Sent folder
    Args:
        subject: Email subject to search for
        recipient: Recipient email address
    Returns:
        True if email deleted successfully, False otherwise
    """
    try:
        # Validate parameters
        if not subject or not recipient:
            print(f"Error deleting sent email: Missing subject or recipient (subject={subject}, recipient={recipient})")
            return False
        
        # IMAP configuration from environment variables
        imap_server = IMAP_SERVER
        imap_port = IMAP_PORT
        username = MAIL_USERNAME
        password = MAIL_PASSWORD
        
        # Check if password is available (required for IMAP)
        if not password:
            print(f"Error deleting sent email: SMTP_PASSWORD not configured")
            return False
        
        # Connect to IMAP server
        import imaplib
        try:
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(username, password)
        except Exception as e:
            print(f"Error connecting to IMAP server: {e}")
            return False
        
        # Select Sent folder
        mail.select('INBOX.Sent')  # OVH uses INBOX.Sent for sent emails
        
        # Search for email with specific subject and recipient
        search_criteria = f'(SUBJECT "{subject}" TO "{recipient}")'
        status, messages = mail.search(None, search_criteria)
        
        if status == 'OK' and messages and messages[0]:
            # Get message IDs - messages[0] might be bytes or string
            message_bytes = messages[0]
            if isinstance(message_bytes, bytes):
                message_str = message_bytes.decode('utf-8')
            else:
                message_str = str(message_bytes) if message_bytes else ''
            
            if message_str.strip():
                message_ids = message_str.split()
                
                # Delete each matching email
                for msg_id in message_ids:
                    mail.store(msg_id, '+FLAGS', '\\Deleted')
                
                # Expunge deleted emails
                mail.expunge()
                mail.close()
                mail.logout()
                return True
        
        mail.close()
        mail.logout()
        return False
            
    except Exception as e:
        print(f"Error deleting sent email: {e}")
        return False

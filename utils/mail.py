import logging
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bootstrap import *

def send_mail(address, service_name):
    try:
        # Create a MIMEMultipart class, and set up the From, To, Subject fields
        html = "<div>"+address['email_message_text']+"<br><b>" + address['email_message_desc'] + "</b></div>"
        receivers = address['email_cc_list']

        email_message = MIMEMultipart()
        email_message['From'] = service_name +' <' + address['email_from'] + '>'
        email_message['To'] = address['email_to']
        email_message['Subject'] = address['subject'] + " - " + address['date']

        email_message.attach(MIMEText(html, "html"))

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(address['email_from'], address['email_password'])
                server.sendmail(address['email_from'], receivers, email_message.as_string())
        except smtplib.SMTPAuthenticationError as e:
            error_msg = """
                In a nutshell, google is not allowing you to log in via smtplib because it has flagged this sort of login as "less secure", so what you have to do is go to this link while you're logged in to your google account, and allow the access:
                https://www.google.com/settings/security/lesssecureapps
                Once that is set (see my screenshot below), it should work.
            """
            logging.critical("SMTPAuthenticationError occured " + error_msg, exc_info=True)
            print("SMTP Error occured: " + str(e) + " " + error_msg)
        except Exception as e:
            logging.error("Exception occured", exc_info=True)
        else:
            print("Mail sent successfully")
    except Exception as e:
        logging.error("Exception occured", exc_info=True)
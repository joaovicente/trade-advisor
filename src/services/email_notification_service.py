import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python

class EmailNotificationService:
    def __init__(self):
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY', None)
        self.email_sender = os.environ.get('EMAIL_SENDER', None)
        self.email_receiver = os.environ.get('EMAIL_RECEIVER', None)
        if any([self.sendgrid_api_key is None, self.email_sender is None, self.email_receiver is None]):
            raise Exception('Missing environment variables SENDGRID_API_KEY, EMAIL_SENDER, EMAIL_RECEIVER')

    def send_email(self, subject, body):
        message = Mail(
            from_email=self.email_sender,
            to_emails=self.email_receiver,
            subject=subject,
            html_content=body
            )
        try:
            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)
            #print(response.status_code)
            #print(response.body)
            #print(response.headers)
        except Exception as e:
            print(e.message)
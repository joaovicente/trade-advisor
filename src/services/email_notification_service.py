import boto3
import os

class EmailNotificationService:
    def __init__(self, email_receiver=None):
        self.ses = boto3.client('ses', region_name='eu-west-1')
        self.email_sender = os.environ.get('EMAIL_SENDER', None)
        if email_receiver is not None:
            self.email_receiver = email_receiver
        else:
            self.email_receiver = os.environ.get('EMAIL_RECEIVER', None)
        if any([self.email_sender is None, self.email_receiver is None]):
            raise Exception('Missing environment variables EMAIL_SENDER, EMAIL_RECEIVER')

    def send_email(self, subject, body):
        try:
            self.ses.send_email(
                Source=self.email_sender,
                Destination={
                    'ToAddresses': [self.email_receiver],
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
        except Exception as e:
            print(e.message)
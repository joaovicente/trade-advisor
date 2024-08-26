from twilio.rest import Client
import os

class WhatsappNotificationService:
    def __init__(self, receiver_number=None):
        if receiver_number is None:
            receiver_number = os.environ.get('WHATSAPP_RECEIVER_NUMBER', None) # format: +35319876543
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID', None)
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN', None)
        sender_number = os.environ.get('WHATSAPP_SENDER_NUMBER', None) # format: +35319876543
        if any([account_sid is None, auth_token is None, sender_number is None, receiver_number is None]):
            raise Exception('Missing environment variables TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, WHATSAPP_SENDER_NUMBER, WHATSAPP_RECEIVER_NUMBER') 
        self.sender = f'whatsapp:{sender_number}' # e.g. "whatsapp:+35319876543"
        self.receiver = f'whatsapp:{receiver_number}' # e.g. "whatsapp:+35319876543"
        self.client = Client(account_sid, auth_token)

    def send_message(self, body):
        #print(f"sending whatsapp message from `{self.sender}` to `{self.receiver}`")
        message = self.client.messages.create(
            from_=self.sender,
            body=body,
            to=self.receiver
        )
        return message.sid
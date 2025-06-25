from celery_app import app
from tasks import process_notification

if __name__ == "__main__":
    # Example: Sending an email notification
    email_payload = {
        "to": "receiver@example.com",
        "subject": "Sample Email",
        "body": "This is a sample email notification",
    }
    result = process_notification.delay("email", email_payload)
    print(f"Task ID: {result.id}")

    # Example: Sending an SMS notification
    sms_payload = {
        "phone_number": "1234567890",
        "message": "This is a sample SMS notification",
    }
    result = process_notification.delay("sms", sms_payload)
    print(f"Task ID: {result.id}")

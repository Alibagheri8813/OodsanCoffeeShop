import logging

logger = logging.getLogger(__name__)


def send_sms(phone_number: str, message: str) -> None:
    """
    Send an SMS to an Iranian phone number. Replace with a real gateway in production.
    For local/dev, we just log the message.
    """
    # Example for real integrations (pseudo):
    # from kavenegar import KavenegarAPI, APIException, HTTPException
    # api = KavenegarAPI(os.environ['KAVENEGAR_API_KEY'])
    # params = { 'receptor': phone_number, 'message': message }
    # api.sms_send(params)

    logger.info(f"[SMS] To: {phone_number} | Message: {message}")
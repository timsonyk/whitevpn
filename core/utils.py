import uuid
import secrets


def generate_token() -> str:
    """Generate a unique token for config URL."""
    return secrets.token_urlsafe(32)


def generate_payment_payload() -> str:
    """Generate a unique payload for payment tracking."""
    return str(uuid.uuid4())

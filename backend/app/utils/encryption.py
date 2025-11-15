"""Fernet encryption utilities for sensitive data (camera passwords, API keys)"""
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Fernet cipher with encryption key from environment
try:
    _cipher = Fernet(settings.ENCRYPTION_KEY.encode())
except Exception as e:
    logger.error(f"Failed to initialize encryption cipher: {e}")
    raise ValueError(
        "Invalid ENCRYPTION_KEY. Generate a new key with: "
        "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    )


def encrypt_password(password: str) -> str:
    """
    Encrypt a password using Fernet (AES-256 symmetric encryption)
    
    Args:
        password: Plain text password to encrypt
        
    Returns:
        Encrypted password prefixed with 'encrypted:' marker
        
    Example:
        >>> encrypt_password("my_secret_123")
        'encrypted:gAAAAABh...'
    """
    if not password:
        return ""
    
    # Avoid double encryption
    if password.startswith("encrypted:"):
        return password
    
    try:
        encrypted_bytes = _cipher.encrypt(password.encode())
        return f"encrypted:{encrypted_bytes.decode()}"
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise ValueError("Failed to encrypt password")


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt a Fernet-encrypted password
    
    Args:
        encrypted_password: Encrypted password string with 'encrypted:' prefix
        
    Returns:
        Plain text password
        
    Raises:
        ValueError: If decryption fails or format is invalid
        
    Example:
        >>> decrypt_password("encrypted:gAAAAABh...")
        'my_secret_123'
    """
    if not encrypted_password:
        return ""
    
    # Return as-is if not encrypted (backward compatibility)
    if not encrypted_password.startswith("encrypted:"):
        logger.warning("Attempted to decrypt non-encrypted password")
        return encrypted_password
    
    # Remove prefix and decrypt
    encrypted_data = encrypted_password.replace("encrypted:", "", 1)
    
    try:
        decrypted_bytes = _cipher.decrypt(encrypted_data.encode())
        return decrypted_bytes.decode()
    except InvalidToken:
        logger.error("Decryption failed: Invalid token or wrong encryption key")
        raise ValueError("Failed to decrypt password - invalid token or wrong encryption key")
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError("Failed to decrypt password")

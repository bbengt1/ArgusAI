"""Unit tests for encryption utilities (Fernet AES-256)"""
import pytest
from app.utils.encryption import encrypt_password, decrypt_password


class TestPasswordEncryption:
    """Test suite for password encryption/decryption"""

    def test_encrypt_password_returns_encrypted_prefix(self):
        """Encrypted password should start with 'encrypted:' marker"""
        password = "my_secret_password_123"
        encrypted = encrypt_password(password)

        assert encrypted.startswith("encrypted:")
        assert encrypted != password

    def test_encrypt_password_produces_different_output(self):
        """Encrypted password should be different from plain text"""
        password = "test_password"
        encrypted = encrypt_password(password)

        assert encrypted != password
        assert len(encrypted) > len(password)

    def test_encrypt_empty_password(self):
        """Empty password should return empty string"""
        encrypted = encrypt_password("")
        assert encrypted == ""

    def test_encrypt_none_password(self):
        """None password should return empty string"""
        encrypted = encrypt_password(None)
        assert encrypted == ""

    def test_encrypt_already_encrypted_password(self):
        """Already encrypted password should not be double-encrypted"""
        password = "test_password"
        encrypted_once = encrypt_password(password)
        encrypted_twice = encrypt_password(encrypted_once)

        assert encrypted_once == encrypted_twice

    def test_decrypt_password_returns_original(self):
        """Decrypted password should match original plain text"""
        original = "my_secret_password_123"
        encrypted = encrypt_password(original)
        decrypted = decrypt_password(encrypted)

        assert decrypted == original

    def test_decrypt_empty_password(self):
        """Empty encrypted password should return empty string"""
        decrypted = decrypt_password("")
        assert decrypted == ""

    def test_decrypt_non_encrypted_password(self):
        """Non-encrypted password should return as-is (backward compatibility)"""
        plain = "plain_text_password"
        decrypted = decrypt_password(plain)

        # Should log warning but return the plain text
        assert decrypted == plain

    def test_decrypt_invalid_encrypted_format(self):
        """Invalid encrypted format should raise ValueError"""
        invalid = "encrypted:invalid_base64_garbage!!!"

        with pytest.raises(ValueError, match="Failed to decrypt password"):
            decrypt_password(invalid)

    def test_roundtrip_encryption_decryption(self):
        """Encrypt then decrypt should return original password"""
        test_passwords = [
            "simple",
            "with spaces and symbols !@#$%",
            "unicode_test_éàü中文",
            "very_long_password_" * 10,
        ]

        for password in test_passwords:
            encrypted = encrypt_password(password)
            decrypted = decrypt_password(encrypted)
            assert decrypted == password, f"Roundtrip failed for: {password}"

# utils/crypto_utils.py
import os
import binascii # Required for specific exception handling
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from base64 import b64encode, b64decode

# AES block size is 128 bits (16 bytes)
AES_BLOCK_SIZE = 16
# Key size can be 128, 192, or 256 bits. We'll aim for AES-256, so 32 bytes.
AES_KEY_SIZE = 32

class CryptoError(Exception):
    """Custom exception for cryptographic errors."""
    pass

def generate_aes_key() -> bytes:
    """Generates a random AES-256 key (32 bytes)."""
    return os.urandom(AES_KEY_SIZE)

def encrypt_aes256(key: bytes, plaintext: bytes) -> bytes:
    """
    Encrypts plaintext using AES-256 CBC mode with PKCS7 padding.
    The IV is prepended to the ciphertext.

    Args:
        key: A 32-byte AES key.
        plaintext: The data to encrypt (bytes).

    Returns:
        Encrypted data as bytes (IV + ciphertext).
    
    Raises:
        CryptoError: If encryption fails or inputs are invalid.
    """
    if not isinstance(key, bytes) or len(key) != AES_KEY_SIZE:
        raise CryptoError(f"Key must be {AES_KEY_SIZE} bytes long.")
    if not isinstance(plaintext, bytes):
        try:
            # Attempt to encode if it's a string, assuming UTF-8
            plaintext = plaintext.encode('utf-8')
        except (AttributeError, UnicodeEncodeError):
            raise CryptoError("Plaintext must be bytes or a UTF-8 encodable string.")

    backend = default_backend()
    iv = os.urandom(AES_BLOCK_SIZE)  # Generate a random IV for each encryption

    # PKCS7 Padding
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_plaintext = padder.update(plaintext) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

    # Prepend IV to ciphertext for use during decryption
    return iv + ciphertext

def decrypt_aes256(key: bytes, encrypted_data: bytes) -> bytes:
    """
    Decrypts data encrypted with AES-256 CBC mode with PKCS7 padding.
    Assumes the IV is prepended to the ciphertext.

    Args:
        key: The 32-byte AES key used for encryption.
        encrypted_data: The data to decrypt (bytes), with IV prepended.

    Returns:
        Decrypted plaintext as bytes.

    Raises:
        CryptoError: If decryption fails (e.g., bad key, corrupted data, padding error).
    """
    if not isinstance(key, bytes) or len(key) != AES_KEY_SIZE:
        raise CryptoError(f"Key must be {AES_KEY_SIZE} bytes long.")
    if not isinstance(encrypted_data, bytes) or len(encrypted_data) < AES_BLOCK_SIZE: # Must be at least as long as IV
        raise CryptoError("Encrypted data is invalid or too short.")

    backend = default_backend()
    
    # Extract IV from the beginning of the encrypted data
    iv = encrypted_data[:AES_BLOCK_SIZE]
    ciphertext = encrypted_data[AES_BLOCK_SIZE:]

    if not ciphertext: # Ensure there is ciphertext after extracting IV
        raise CryptoError("Ciphertext is missing after IV extraction.")

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()
    
    try:
        decrypted_padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    except ValueError as e: # Often indicates issues with key or data
        raise CryptoError(f"Decryption failed. Check key or data integrity: {str(e)}")


    # PKCS7 Unpadding
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    try:
        plaintext = unpadder.update(decrypted_padded_plaintext) + unpadder.finalize()
    except ValueError:
        # This typically means incorrect padding, which can happen with a wrong key
        # or corrupted ciphertext.
        raise CryptoError("Decryption failed due to incorrect padding. Check key or data integrity.")
        
    return plaintext

# Helper functions for string/base64 encoding convenience
def encrypt_aes256_str(key: bytes, text_data: str) -> str:
    """Encrypts a string and returns base64 encoded ciphertext."""
    if not isinstance(text_data, str):
        raise CryptoError("Input for encrypt_aes256_str must be a string.")
    encrypted_bytes = encrypt_aes256(key, text_data.encode('utf-8'))
    return b64encode(encrypted_bytes).decode('utf-8')

def decrypt_aes256_str(key: bytes, base64_ciphertext: str) -> str:
    """Decrypts base64 encoded ciphertext and returns a string."""
    if not isinstance(base64_ciphertext, str):
        raise CryptoError("Input for decrypt_aes256_str must be a base64 encoded string.")
    
    try:
        # Ensure the input string is UTF-8 encodable for b64decode
        encrypted_bytes_input = base64_ciphertext.encode('utf-8')
        encrypted_bytes = b64decode(encrypted_bytes_input)
    except (binascii.Error, UnicodeEncodeError) as e:
        # Catch specific errors related to base64 decoding or encoding the input string
        raise CryptoError(f"Invalid base64 data or string encoding: {str(e)}")
    
    # Now, encrypted_bytes contains the result of b64decode.
    # The length check within decrypt_aes256 will handle cases where the decoded
    # bytes are too short (e.g. if base64_ciphertext was "QQ==" which decodes to one byte).
    # If b64decode produced garbage that happens to be long enough but still invalid
    # for decryption, decrypt_aes256 will raise an appropriate CryptoError.

    decrypted_bytes = decrypt_aes256(key, encrypted_bytes)
    try:
        return decrypted_bytes.decode('utf-8')
    except UnicodeDecodeError:
        raise CryptoError("Failed to decode decrypted bytes to UTF-8 string. Data may not be text.")

if __name__ == '__main__':
    # Example Usage (for demonstration and basic testing)
    try:
        # Key management is crucial. In a real app, this key would come from a secure store.
        # For this example, we generate one.
        example_key = generate_aes_key()
        print(f"Generated AES Key (hex): {example_key.hex()}")

        original_text = "これは秘密のメッセージです。This is a secret message."
        print(f"Original text: {original_text}")

        # Using string helpers
        b64_cipher = encrypt_aes256_str(example_key, original_text)
        print(f"Base64 Encrypted: {b64_cipher}")

        decrypted_text = decrypt_aes256_str(example_key, b64_cipher)
        print(f"Decrypted text: {decrypted_text}")

        assert original_text == decrypted_text
        print("String encryption/decryption test PASSED!")

        # Using bytes helpers
        original_bytes = b"Some binary data \x00\x01\x02\x03"
        print(f"Original bytes: {original_bytes!r}") # !r for unambiguous representation
        
        encrypted_bytes_direct = encrypt_aes256(example_key, original_bytes)
        print(f"Direct Encrypted (hex): {encrypted_bytes_direct.hex()}")
        
        decrypted_bytes_direct = decrypt_aes256(example_key, encrypted_bytes_direct)
        print(f"Direct Decrypted: {decrypted_bytes_direct!r}")

        assert original_bytes == decrypted_bytes_direct
        print("Bytes encryption/decryption test PASSED!")

        # Test error cases
        print("\nTesting error handling...")
        try:
            decrypt_aes256_str(generate_aes_key(), b64_cipher) # Using wrong key
        except CryptoError as e:
            print(f"Caught expected error (wrong key): {e}")
        
        try:
            decrypt_aes256_str(example_key, "InvalidBase64NotReally")
        except CryptoError as e:
            print(f"Caught expected error (invalid base64): {e}")

        try:
            encrypt_aes256(b"shortkey", original_text.encode())
        except CryptoError as e:
            print(f"Caught expected error (invalid key length): {e}")

    except CryptoError as e:
        print(f"Crypto Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# tests/unit/test_crypto_utils.py
import unittest
import os

# Adjust sys.path to allow importing from the 'utils' directory
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.crypto_utils import (
    generate_aes_key,
    encrypt_aes256,
    decrypt_aes256,
    encrypt_aes256_str,
    decrypt_aes256_str,
    CryptoError,
    AES_KEY_SIZE
)

class TestCryptoUtils(unittest.TestCase):

    def test_generate_aes_key(self):
        key = generate_aes_key()
        self.assertIsInstance(key, bytes)
        self.assertEqual(len(key), AES_KEY_SIZE) # AES-256 key is 32 bytes

    def test_string_encryption_decryption_roundtrip(self):
        key = generate_aes_key()
        original_text = "This is a secret message for testing purposes. これは秘密のメッセージです。"
        
        encrypted_b64 = encrypt_aes256_str(key, original_text)
        self.assertIsInstance(encrypted_b64, str)
        
        decrypted_text = decrypt_aes256_str(key, encrypted_b64)
        self.assertEqual(original_text, decrypted_text)

    def test_bytes_encryption_decryption_roundtrip(self):
        key = generate_aes_key()
        original_bytes = b"Some important binary data \x00\x01\x02\xff\xfe" # Corrected invalid UTF-8 sequence for direct bytes
        
        encrypted_data = encrypt_aes256(key, original_bytes)
        self.assertIsInstance(encrypted_data, bytes)
        # IV (16 bytes) + Ciphertext (at least 1 block = 16 bytes, possibly more due to padding)
        self.assertTrue(len(encrypted_data) >= 16 + 16) # AES_BLOCK_SIZE for IV + at least one block for data
        
        decrypted_bytes = decrypt_aes256(key, encrypted_data)
        self.assertEqual(original_bytes, decrypted_bytes)

    def test_decrypt_with_wrong_key_str(self):
        key1 = generate_aes_key()
        key2 = generate_aes_key()
        self.assertNotEqual(key1, key2) # Ensure keys are different

        original_text = "A message to be kept secret."
        encrypted_b64 = encrypt_aes256_str(key1, original_text)
        
        with self.assertRaisesRegex(CryptoError, "Decryption failed"):
            # Error could be "incorrect padding" or "failed. Check key or data integrity"
            decrypt_aes256_str(key2, encrypted_b64)

    def test_decrypt_with_wrong_key_bytes(self):
        key1 = generate_aes_key()
        key2 = generate_aes_key()
        self.assertNotEqual(key1, key2)

        original_bytes = b"Another set of bytes \x10\x00" # Corrected invalid UTF-8 sequence
        encrypted_data = encrypt_aes256(key1, original_bytes)
        
        with self.assertRaisesRegex(CryptoError, "Decryption failed"):
            decrypt_aes256(key2, encrypted_data)

    def test_decrypt_corrupted_ciphertext_str(self):
        key = generate_aes_key()
        original_text = "Valid message"
        encrypted_b64 = encrypt_aes256_str(key, original_text)
        
        # Corrupt the base64 string
        corrupted_b64 = encrypted_b64[:-5] + "XXXXX" 
        if corrupted_b64 == encrypted_b64 : # ensure it's actually different
             corrupted_b64 = "totally_invalid_base64_$$$$"

        with self.assertRaises(CryptoError): # Could be base64 error or decryption error
            decrypt_aes256_str(key, corrupted_b64)

    def test_decrypt_corrupted_ciphertext_bytes(self):
        key = generate_aes_key()
        original_bytes = b"Valid bytes"
        encrypted_data = encrypt_aes256(key, original_bytes)

        # Corrupt the bytes (e.g., flip some bits in the ciphertext part)
        iv_part = encrypted_data[:16]
        ciphertext_part = bytearray(encrypted_data[16:])
        if len(ciphertext_part) > 0 :
            ciphertext_part[0] = ciphertext_part[0] ^ 0xFF # Flip first byte
        corrupted_data = iv_part + bytes(ciphertext_part)
        
        if corrupted_data == encrypted_data and len(ciphertext_part) > 0: # if flipping didn't change it (e.g. single byte FF)
            # Create more distinct corruption if previous was too subtle
            corrupted_data = iv_part + os.urandom(len(ciphertext_part))


        with self.assertRaisesRegex(CryptoError, "Decryption failed"):
            decrypt_aes256(key, corrupted_data)
            
    def test_encrypt_empty_string(self):
        key = generate_aes_key()
        original_text = ""
        encrypted_b64 = encrypt_aes256_str(key, original_text)
        decrypted_text = decrypt_aes256_str(key, encrypted_b64)
        self.assertEqual(original_text, decrypted_text)

    def test_encrypt_empty_bytes(self):
        key = generate_aes_key()
        original_bytes = b""
        encrypted_data = encrypt_aes256(key, original_bytes)
        decrypted_bytes = decrypt_aes256(key, encrypted_data)
        self.assertEqual(original_bytes, decrypted_bytes)

    def test_invalid_key_length(self):
        short_key = os.urandom(AES_KEY_SIZE - 1)
        long_key = os.urandom(AES_KEY_SIZE + 1)
        valid_plaintext_bytes = b"test"
        # Construct a plausible encrypted data structure: IV (16 bytes) + some data (16 bytes)
        dummy_encrypted_data = os.urandom(16) + os.urandom(16)


        with self.assertRaisesRegex(CryptoError, f"Key must be {AES_KEY_SIZE} bytes long."):
            encrypt_aes256(short_key, valid_plaintext_bytes)
        with self.assertRaisesRegex(CryptoError, f"Key must be {AES_KEY_SIZE} bytes long."):
            decrypt_aes256(short_key, dummy_encrypted_data) 
        
        with self.assertRaisesRegex(CryptoError, f"Key must be {AES_KEY_SIZE} bytes long."):
            encrypt_aes256(long_key, valid_plaintext_bytes)
        with self.assertRaisesRegex(CryptoError, f"Key must be {AES_KEY_SIZE} bytes long."):
            decrypt_aes256(long_key, dummy_encrypted_data)

    def test_invalid_plaintext_type_encrypt(self):
        key = generate_aes_key()
        with self.assertRaisesRegex(CryptoError, "Plaintext must be bytes or a UTF-8 encodable string."):
            encrypt_aes256(key, 12345) # Pass an integer

    def test_invalid_encrypted_data_type_decrypt(self):
        key = generate_aes_key()
        with self.assertRaisesRegex(CryptoError, "Encrypted data is invalid or too short."):
            decrypt_aes256(key, "not bytes") # type: ignore
        with self.assertRaisesRegex(CryptoError, "Encrypted data is invalid or too short."):
            decrypt_aes256(key, b"short") # Shorter than IV

    def test_invalid_base64_input_decrypt_str(self):
        key = generate_aes_key()
        with self.assertRaisesRegex(CryptoError, "Encrypted data is invalid or too short."): # Changed line
            decrypt_aes256_str(key, "This is not valid base64!@#$")

    def test_non_utf8_decryption_str(self):
        key = generate_aes_key()
        # Encrypt raw non-UTF-8 bytes (e.g., Shift-JIS "あいう")
        # These bytes are: b'\x82\xa0\x82\xa2\x82\xa4'
        non_utf8_bytes = b'\x82\xa0\x82\xa2\x82\xa4' 
        
        encrypted_non_utf8_payload = encrypt_aes256(key, non_utf8_bytes)
        
        # We need b64encode for this test case. It's imported in __main__ but not at class level.
        # For robustness in testing environments, ensure it's available or mock if necessary.
        try:
            from base64 import b64encode
            b64_encrypted_non_utf8 = b64encode(encrypted_non_utf8_payload).decode('ascii')
            
            with self.assertRaisesRegex(CryptoError, "Failed to decode decrypted bytes to UTF-8 string"):
                decrypt_aes256_str(key, b64_encrypted_non_utf8)
        except ImportError:
            self.skipTest("base64.b64encode not available in test scope to properly run test_non_utf8_decryption_str")


if __name__ == '__main__':
    # Need to explicitly import b64encode for the last test case if run directly
    from base64 import b64encode # This makes it available in the module's global scope when run as script
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

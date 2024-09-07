import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class Crypto:
    def __init__(self, password, salt):
        self.salt = salt

    def derive_key(self):
        """
        Derive an encryption key from the user's password and salt using PBKDF2.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(self.password.encode())

    def encrypt(self, plaintext):
        """
        Encrypt the given plaintext using AES-256-GCM.
        """
        key = self.derive_key()
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return iv + encryptor.tag + ciphertext

    def decrypt(self, encrypted_data):
        """
        Decrypt the given encrypted data using AES-256-GCM.
        """
        key = self.derive_key()
        iv = encrypted_data[:12]
        tag = encrypted_data[12:28]
        ciphertext = encrypted_data[28:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()


# # Encrypt an API key
# user_password = "mySecurePassword"
# api_key = "abc123def456ghi789"

# crypto = Crypto(user_password)
# encrypted_api_key = crypto.encrypt(api_key)

# # Store the encrypted API key and the salt in your database or other storage
# # ...
# encrypted_data_for_storage = encrypted_api_key
# user_salt_for_storage = crypto.salt

# # Retrieve and decrypt the API key when needed
# crypto = Crypto(user_password, user_salt_for_storage)
# decrypted_api_key = crypto.decrypt(encrypted_data_for_storage)
# print(f"Decrypted API key: {decrypted_api_key}")

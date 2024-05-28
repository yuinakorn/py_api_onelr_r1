from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import os
import base64

from models.preg_crypto.pregs_crypto_model import EncryptInput, DecryptInput

from dotenv import dotenv_values

config_env = dotenv_values(".env")


# Function to generate salt
def generate_salt():
    return os.urandom(16)  # 16 bytes for salt


# Function to derive key from password and salt
def derive_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32 bytes for key
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


# Function to encrypt data
async def encrypt_data(datas):
    password = config_env["PASSWORD_KEY"]
    salt = generate_salt()
    key = derive_key(password, salt)
    cipher = Fernet(key)
    encrypted_cid = cipher.encrypt(datas.cid.encode())
    encrypted_pname = cipher.encrypt(datas.pname.encode())
    encrypted_lname = cipher.encrypt(datas.lname.encode())
    return {
        "encrypted_cid": encrypted_cid.decode(),
        "encrypted_pname": encrypted_pname.decode(),
        "encrypted_lname": encrypted_lname.decode(),
        "salt": base64.urlsafe_b64encode(salt)
    }

    
async def decrypt_data(datas):
    password = config_env["PASSWORD_KEY"]
    try:
        salt = base64.urlsafe_b64decode(datas.salt)
        key = derive_key(password, salt)
        cipher = Fernet(key)
        decrypted_cid = cipher.decrypt(datas.cid.encode())
        decrypted_pname = cipher.decrypt(datas.pname.encode())
        decrypted_lname = cipher.decrypt(datas.lname.encode())
        return {
            "cid": decrypted_cid.decode(),
            "pname": decrypted_pname.decode(),
            "lname": decrypted_lname.decode()
        }
    except Exception as e:
        # If decryption fails, return plain text
        return {
            "cid": datas.cid,
            "pname": datas.pname,
            "lname": datas.lname
        }



async def plain_to_cipher(datas):
    pass


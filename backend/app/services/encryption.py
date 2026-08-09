"""Fernet対称暗号化（ユーザーID + サーバーシークレットから鍵を導出）"""
import base64
import hashlib
from cryptography.fernet import Fernet


def _derive_key(user_id: str, secret: str) -> bytes:
    """PBKDF2でユーザー固有の256bit鍵を生成する"""
    material = f"{user_id}:{secret}".encode()
    digest = hashlib.pbkdf2_hmac("sha256", material, b"personality-chat-salt", 100_000)
    return base64.urlsafe_b64encode(digest)


def encrypt(plaintext: str, user_id: str, secret: str) -> str:
    key = _derive_key(user_id, secret)
    f = Fernet(key)
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str, user_id: str, secret: str) -> str:
    key = _derive_key(user_id, secret)
    f = Fernet(key)
    return f.decrypt(ciphertext.encode()).decode()

from app.services.encryption import encrypt, decrypt


def test_encrypt_decrypt_roundtrip():
    user_id = "test-user-123"
    secret = "test-secret-key!!"
    text = "こんにちは、世界！"
    cipher = encrypt(text, user_id, secret)
    assert cipher != text
    assert decrypt(cipher, user_id, secret) == text


def test_different_user_cannot_decrypt():
    import pytest
    user_id = "user-a"
    secret = "secret"
    cipher = encrypt("秘密のメッセージ", user_id, secret)
    with pytest.raises(Exception):
        decrypt(cipher, "user-b", secret)

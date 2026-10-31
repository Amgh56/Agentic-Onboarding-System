from app.core.crypto import decrypt, encrypt


def test_encrypt_round_trip():
    secret = "abcd efgh ijkl mnop"
    stored = encrypt(secret)
    assert stored != secret
    assert decrypt(stored) == secret

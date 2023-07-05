import hashlib


def hash_pw(password):
    x = hashlib.sha256()
    x.update(password.encode())
    return x.hexdigest()

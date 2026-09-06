"""Génère JWT_SECRET et ENCRYPTION_MASTER_KEY pour .env.

Usage : python -m app.scripts.genkeys
"""
import os
import secrets

def gen() -> None:
    print("JWT_SECRET=" + secrets.token_hex(64))
    print("ENCRYPTION_MASTER_KEY=" + secrets.token_hex(32))
    print("\n# À reporter dans .env (remplacer les valeurs vides actuelles)")


if __name__ == "__main__":
    gen()
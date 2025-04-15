#
#  generate_rsa_keys.py
#  fastapi_kafka
#
#  Created by Xavier Cañadas on 15/4/2025
#  Copyright (c) 2025. All rights reserved.

import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Generate keys (run this once to create keys)
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Save private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Save public key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    os.makedirs("./keys", exist_ok=True)

    with open("./keys/private_key.pem", "wb") as f:
        f.write(private_pem)

    with open("./keys/public_key.pem", "wb") as f:
        f.write(public_pem)

    with open("./keys/public_key.pem", "wb") as f:
        f.write(public_pem)

# Run this function once to generate keys
if __name__ == "__main__":
    generate_rsa_keys()


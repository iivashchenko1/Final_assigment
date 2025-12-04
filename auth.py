"""
Authentication helpers for the chat application.

This module is responsible for hashing passwords when users
create accounts and for verifying passwords during login.
"""

import os 
import hashlib #Gives an access to a Hash functions 
from typing import Tuple


def hash_password(password: str) -> Tuple[str, str]: #return a tuple of salt_hex and hash_hex
    """
    Convert a plain-text password into a (salt, hash) pair.

    The salt and hash are returned as hexadecimal strings so that
    they can be stored easily in a TEXT column in the database.
    """
    # 1. Generate a random 16-byte salt using a cryptographically
    #    secure random number generator.
    salt = os.urandom(16)

    # 2. Derive a secure hash from the password and salt using
    #    PBKDF2-HMAC with SHA-256.
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",              # Name of the hash function.
        password.encode("utf-8"),  # Password converted to bytes.
        salt,                  # The random salt.
        100_000,               # Number of iterations (100k).
    )

    # 3. Convert salt and hash to hex strings for storage.
    salt_hex = salt.hex()
    hash_hex = hash_bytes.hex()

    return salt_hex, hash_hex


def verify_password(password: str, salt_hex: str, stored_hash_hex: str) -> bool: # return True or False
    """
    Verify that a plain-text password matches the stored hash.

    Args:
        password: The password provided by the user during login.
        salt_hex: The salt stored in the database (hex string).
        stored_hash_hex: The password hash stored in the database (hex string).

    Returns:
        True if the password is correct, False otherwise.
    """
    # 1. Convert the hex-encoded salt back into bytes.
    salt = bytes.fromhex(salt_hex)

    # 2. Recompute the hash using the same parameters as in hash_password.
    new_hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000,
    )
    #We used exact the same parameters as for hash_pasword . The only difference is : the password is whatever user types during login.

    # 3. Convert the new hash to hex and compare with the stored hash.
    new_hash_hex = new_hash_bytes.hex()

    return new_hash_hex == stored_hash_hex
"""
If they are equal = login success
if they are different = wrong password
"""





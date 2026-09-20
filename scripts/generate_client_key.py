#!/usr/bin/env python3
import hashlib
import secrets


token = "jev_" + secrets.token_urlsafe(32)
print("Customer token (show once):", token)
print("CLIENT_KEY_HASHES value:", hashlib.sha256(token.encode()).hexdigest())

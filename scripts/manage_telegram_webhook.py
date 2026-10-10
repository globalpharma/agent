#!/usr/bin/env python3
"""
Diagnostic and fix script for Telegram Bot API webhook & getUpdates conflicts.
Extracts token from PostgreSQL channel_instances (handling both plain JSON and AES-GCM encrypted),
inspects getMe, getWebhookInfo, and calls deleteWebhook?drop_pending_updates=true.
"""
import os
import sys
import json
import base64
import binascii
import urllib.request
import urllib.error

def derive_key(k: str) -> bytes:
    if len(k) == 64:
        return binascii.unhexlify(k)
    if len(k) == 44 and k.endswith("="):
        b = base64.b64decode(k)
        if len(b) == 32:
            return b
    if len(k) == 32:
        return k.encode("utf-8")
    raise ValueError(f"Invalid key length: {len(k)}")

def decrypt_val(ciphertext: str, key_str: str) -> str:
    if not key_str or not ciphertext:
        return ciphertext
    if not ciphertext.startswith("aes-gcm:"):
        return ciphertext
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "cryptography"])
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key_bytes = derive_key(key_str)
    raw = base64.b64decode(ciphertext[len("aes-gcm:"):])
    nonce = raw[:12]
    ct_tag = raw[12:]
    aesgcm = AESGCM(key_bytes)
    return aesgcm.decrypt(nonce, ct_tag, None).decode("utf-8")

def parse_credentials(raw_str: str, enc_key: str) -> dict:
    raw_str = raw_str.strip()
    if raw_str.startswith("aes-gcm:"):
        decrypted = decrypt_val(raw_str, enc_key)
        return json.loads(decrypted)
    return json.loads(raw_str)

def main():
    if len(sys.argv) < 2:
        print("Usage: manage_telegram_webhook.py <raw_credentials_string>")
        sys.exit(1)

    raw_creds = sys.argv[1]
    enc_key = os.getenv("GOCLAW_ENCRYPTION_KEY", "")

    try:
        creds = parse_credentials(raw_creds, enc_key)
        token = creds.get("token")
        if not token:
            print("[ERROR] No token found in credentials object:", creds)
            sys.exit(1)
        
        # Masked token for logs
        masked = token[:6] + "..." + token[-4:] if len(token) > 10 else "***"
        print(f"[OK] Successfully extracted Telegram Bot Token: {masked}")

        # 1. getMe
        try:
            req = urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
            me = json.loads(req.read().decode())
            print("[getMe Result]:", json.dumps(me, ensure_ascii=False))
        except Exception as e:
            print("[getMe Error]:", e)

        # 2. getWebhookInfo
        try:
            req = urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
            wh = json.loads(req.read().decode())
            print("[getWebhookInfo Result]:", json.dumps(wh, ensure_ascii=False))
        except Exception as e:
            print("[getWebhookInfo Error]:", e)

        # 3. deleteWebhook with drop_pending_updates=true
        try:
            req = urllib.request.urlopen(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true", timeout=10)
            dw = json.loads(req.read().decode())
            print("[deleteWebhook Result]:", json.dumps(dw, ensure_ascii=False))
        except Exception as e:
            print("[deleteWebhook Error]:", e)

    except Exception as e:
        print(f"[ERROR] Failed to process credentials: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

"""Validate webhook (Alexa/VoiceMonkey) connectivity.

Sends test messages to verify that the webhook is working.

Usage:
    python validate_webhook.py                       # sends configured alert phrases
    python validate_webhook.py "minha mensagem"      # sends a custom message
"""

import sys
import time

import requests
import yaml

from src.alert_engine import build_message


def load_config() -> dict | None:
    try:
        with open("config.yaml") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("ERROR: config.yaml not found.")
        print("Copy config.example.yaml to config.yaml and fill in your values.")
        return None


def get_webhook_config(config: dict) -> dict | None:
    for out_cfg in config.get("outputs", []):
        if out_cfg.get("type") == "webhook":
            return out_cfg
    print("ERROR: No webhook output found in config.yaml.")
    return None


def send_message(url: str, payload: dict) -> bool:
    safe_payload = {**payload, "token": payload["token"][:8] + "***"}
    print(f"    Payload: {safe_payload}")
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"    Response: {resp.status_code} {resp.text[:300]}")
        return resp.ok
    except requests.RequestException as e:
        print(f"    ERROR: {e}")
        return False


TEST_SCENARIOS = [
    {"level": "low", "glucose_value": 55, "trend": "↓"},
    {"level": "high", "glucose_value": 210, "trend": "↑"},
]


def main() -> None:
    custom_message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""

    print("=" * 50)
    print("Webhook (Alexa/VoiceMonkey) Validation")
    print("=" * 50)

    print("\n[1] Loading config...")
    config = load_config()
    if config is None:
        sys.exit(1)

    wh_cfg = get_webhook_config(config)
    if wh_cfg is None:
        sys.exit(1)

    url = wh_cfg.get("url", "")
    token = wh_cfg.get("token", "")
    device = wh_cfg.get("device", "")
    language = wh_cfg.get("language", "")

    if not url:
        print("  ERROR: url is empty")
        sys.exit(1)

    print(f"  URL: {url}")
    print(f"  Device: {device}")
    print(f"  Token: {token[:8]}***" if len(token) > 8 else f"  Token: {'(empty)' if not token else token}")
    if language:
        print(f"  Language: {language}")

    base_payload = {"token": token, "device": device}
    if language:
        base_payload["language"] = language

    if custom_message:
        print(f"\n[2] Sending custom message...")
        print(f"    Message: \"{custom_message}\"")
        payload = {**base_payload, "text": custom_message}
        ok = send_message(url, payload)
    else:
        print(f"\n[2] Sending {len(TEST_SCENARIOS)} configured alert phrases...")
        ok = True
        for i, scenario in enumerate(TEST_SCENARIOS, 1):
            message = build_message(
                glucose_value=scenario["glucose_value"],
                level=scenario["level"],
                trend_arrow=scenario["trend"],
                config=config,
            )
            print(f"\n  [{i}/{len(TEST_SCENARIOS)}] {scenario['level'].upper()} alert:")
            print(f"    Message: \"{message}\"")
            payload = {**base_payload, "text": message}
            if not send_message(url, payload):
                ok = False
            if i < len(TEST_SCENARIOS):
                print("    Waiting 5s...")
                time.sleep(5)

    print("\n" + "=" * 50)
    if ok:
        print(">>> SUCCESS <<<")
    else:
        print(">>> FAILURE <<<")
    print("=" * 50)

    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()

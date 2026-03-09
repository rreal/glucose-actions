"""Validate webhook (Alexa/VoiceMonkey) connectivity.

Sends test messages using the configured alert phrases to verify
that the webhook URL, token, device, and messages are working.

Usage:
    python validate_webhook.py
"""

import sys
import time

import yaml

from src.alert_engine import build_message
from src.outputs.webhook import WebhookOutput


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


TEST_SCENARIOS = [
    {"level": "low", "glucose_value": 55, "trend": "↓"},
    {"level": "high", "glucose_value": 210, "trend": "↑"},
]


def main() -> None:
    print("=" * 50)
    print("Webhook (Alexa/VoiceMonkey) Validation")
    print("=" * 50)

    # Load config
    print("\n[1/3] Loading config...")
    config = load_config()
    if config is None:
        print("\n>>> FAILURE <<<")
        sys.exit(1)

    wh_cfg = get_webhook_config(config)
    if wh_cfg is None:
        print("\n>>> FAILURE <<<")
        sys.exit(1)

    url = wh_cfg.get("url", "")
    token = wh_cfg.get("token", "")
    device = wh_cfg.get("device", "")

    if not url:
        print("  ERROR: url is empty")
        print("\n>>> FAILURE <<<")
        sys.exit(1)

    print(f"  URL: {url}")
    print(f"  Device: {device}")
    print(f"  Token: {token[:8]}***" if len(token) > 8 else f"  Token: {'(empty)' if not token else token}")

    # Create output
    print("\n[2/3] Creating webhook output...")
    output = WebhookOutput(url=url, token=token, device=device)

    # Send configured alert messages
    total = len(TEST_SCENARIOS)
    print(f"\n[3/3] Sending {total} test messages (configured alert phrases)...")

    all_ok = True
    for i, scenario in enumerate(TEST_SCENARIOS, 1):
        message = build_message(
            glucose_value=scenario["glucose_value"],
            level=scenario["level"],
            trend_arrow=scenario["trend"],
            config=config,
        )
        print(f"\n  [{i}/{total}] {scenario['level'].upper()} alert:")
        print(f"    \"{message}\"")

        success = output.send_alert(message, glucose_value=scenario["glucose_value"], level=scenario["level"])
        if success:
            print(f"    -> Sent OK")
        else:
            print(f"    -> FAILED")
            all_ok = False

        if i < total:
            print("    Waiting 5s before next message...")
            time.sleep(5)

    if all_ok:
        print("\n" + "=" * 50)
        print(">>> SUCCESS <<<")
        print("=" * 50)
        print(f"\n{total} messages sent to device.")
        print("Check if Alexa spoke each message!")
    else:
        print("\n" + "=" * 50)
        print(">>> FAILURE <<<")
        print("=" * 50)
        print("\nSome messages failed. Check:")
        print("  - Is the URL correct?")
        print("  - Is the token valid?")
        print("  - Is the device name correct in VoiceMonkey?")
        sys.exit(1)


if __name__ == "__main__":
    main()

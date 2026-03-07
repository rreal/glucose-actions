"""Validate webhook (Alexa/VoiceMonkey) connectivity.

Sends a test message to verify that the webhook URL, token,
and device are correctly configured.

Usage:
    python validate_webhook.py
"""

import os
import sys

import yaml

from src.outputs.webhook import WebhookOutput


def load_webhook_config() -> dict | None:
    """Find the first webhook output config."""
    try:
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("ERROR: config.yaml not found.")
        print("Copy config.example.yaml to config.yaml and fill in your values.")
        return None

    for out_cfg in config.get("outputs", []):
        if out_cfg.get("type") == "webhook":
            return out_cfg

    print("ERROR: No webhook output found in config.yaml.")
    return None


def main() -> None:
    print("=" * 50)
    print("Webhook (Alexa/VoiceMonkey) Validation")
    print("=" * 50)

    # Load config
    print("\n[1/3] Loading webhook config...")
    wh_cfg = load_webhook_config()
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

    # Send test message
    print("\n[3/3] Sending test message...")
    test_message = "Teste de conexao: sistema de monitoramento de glicose funcionando corretamente."
    success = output.send_alert(test_message, glucose_value=100, level="normal")

    if success:
        print("\n" + "=" * 50)
        print(">>> SUCCESS <<<")
        print("=" * 50)
        print("\nMensagem de teste enviada para o dispositivo.")
        print("Verifique se a Alexa falou a mensagem!")
    else:
        print("\n" + "=" * 50)
        print(">>> FAILURE <<<")
        print("=" * 50)
        print("\nA mensagem nao foi enviada. Verifique:")
        print("  - A URL esta correta?")
        print("  - O token esta valido?")
        print("  - O device name esta correto no VoiceMonkey?")
        sys.exit(1)


if __name__ == "__main__":
    main()

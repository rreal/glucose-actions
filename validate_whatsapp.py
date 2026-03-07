"""Validate WhatsApp Cloud API connectivity.

Sends a test template message to verify that credentials,
phone number, and template are correctly configured.

Usage:
    python validate_whatsapp.py
"""

import os
import sys

import yaml

from src.outputs.whatsapp import WhatsAppOutput


def load_whatsapp_config() -> dict | None:
    """Find the first whatsapp output config."""
    try:
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("ERROR: config.yaml not found.")
        print("Copy config.example.yaml to config.yaml and fill in your values.")
        return None

    for out_cfg in config.get("outputs", []):
        if out_cfg.get("type") == "whatsapp":
            return out_cfg

    print("ERROR: No whatsapp output found in config.yaml.")
    return None


def main() -> None:
    print("=" * 50)
    print("WhatsApp Cloud API Validation")
    print("=" * 50)

    # Load config
    print("\n[1/3] Loading WhatsApp config...")
    wa_cfg = load_whatsapp_config()
    if wa_cfg is None:
        print("\n>>> FAILURE <<<")
        sys.exit(1)

    phone_number_id = wa_cfg.get("phone_number_id", "")
    access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN") or wa_cfg.get("access_token", "")
    recipient = wa_cfg.get("recipient", "")
    template_name = wa_cfg.get("template_name", "glucose_alert")
    language_code = wa_cfg.get("language_code", "pt_BR")

    if not phone_number_id:
        print("  ERROR: phone_number_id is empty")
        print("\n>>> FAILURE <<<")
        sys.exit(1)
    if not access_token:
        print("  ERROR: access_token is empty (set in config or WHATSAPP_ACCESS_TOKEN env var)")
        print("\n>>> FAILURE <<<")
        sys.exit(1)
    if not recipient:
        print("  ERROR: recipient is empty")
        print("\n>>> FAILURE <<<")
        sys.exit(1)

    print(f"  Phone Number ID: {phone_number_id}")
    print(f"  Recipient: {recipient[:5]}***{recipient[-2:]}")
    print(f"  Template: {template_name} ({language_code})")
    print(f"  Token: {access_token[:8]}***")

    # Create output
    print("\n[2/3] Creating WhatsApp output...")
    output = WhatsAppOutput(
        phone_number_id=phone_number_id,
        access_token=access_token,
        recipient=recipient,
        template_name=template_name,
        language_code=language_code,
    )

    # Send test message
    print("\n[3/3] Sending test message...")
    test_message = "Connection test: glucose monitoring system is working correctly."
    success = output.send_alert(test_message, glucose_value=100, level="normal")

    if success:
        print("\n" + "=" * 50)
        print(">>> SUCCESS <<<")
        print("=" * 50)
        print(f"\nTest message sent to {recipient}.")
        print("Check your WhatsApp!")
    else:
        print("\n" + "=" * 50)
        print(">>> FAILURE <<<")
        print("=" * 50)
        print("\nMessage was not sent. Check:")
        print("  - Is the access_token valid and not expired?")
        print("  - Is the phone_number_id correct?")
        print("  - Is the template '{}' approved in Meta Business Manager?".format(template_name))
        print("  - Is the recipient number registered (development mode)?")
        print("\nTip: run with DEBUG for more details:")
        print("  PYTHONPATH=. python -c \"import logging; logging.basicConfig(level='DEBUG')\" && python validate_whatsapp.py")
        sys.exit(1)


if __name__ == "__main__":
    main()

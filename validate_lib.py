"""Phase 0: Validate pylibrelinkup connectivity and data extraction.

Run this script to test if the pylibrelinkup library can connect to
LibreLinkUp and retrieve glucose data. The result decides the
implementation path (lib vs RPA).

Usage:
    python validate_lib.py
"""

import os
import sys
from datetime import datetime, timezone

import yaml
from pylibrelinkup import PyLibreLinkUp


def load_credentials() -> tuple[str, str]:
    email = os.environ.get("LIBRELINKUP_EMAIL")
    password = os.environ.get("LIBRELINKUP_PASSWORD")

    if not email or not password:
        with open("config.yaml") as f:
            config = yaml.safe_load(f)
        email = email or config["librelinkup"]["email"]
        password = password or config["librelinkup"]["password"]

    return email, password


def main() -> None:
    print("=" * 50)
    print("LibreLinkUp Validation - Phase 0")
    print("=" * 50)

    try:
        # Step 1: Load credentials
        print("\n[1/4] Loading credentials...")
        email, password = load_credentials()
        if not email or not password:
            print("ERROR: Email or password is empty.")
            print("Set them in config.yaml or via LIBRELINKUP_EMAIL/LIBRELINKUP_PASSWORD env vars.")
            print("\n>>> FAILURE <<<")
            sys.exit(1)
        print(f"  Email: {email[:3]}***{email[email.index('@'):]}")

        # Step 2: Authenticate
        print("\n[2/4] Authenticating...")
        client = PyLibreLinkUp(email=email, password=password)
        client.authenticate()
        print("  Authentication successful.")

        # Step 3: Get patients
        print("\n[3/4] Getting patients...")
        patients = client.get_patients()
        if not patients:
            print("  ERROR: No patients found. Make sure someone has shared their LibreLinkUp data with you.")
            print("\n>>> FAILURE <<<")
            sys.exit(1)
        print(f"  Found {len(patients)} patient(s):")
        for i, patient in enumerate(patients):
            print(f"    [{i}] {patient.first_name} {patient.last_name} (ID: {patient.patient_id})")

        # Step 4: Get latest glucose for first patient
        print(f"\n[4/4] Reading latest glucose for {patients[0].first_name}...")
        latest = client.latest(patients[0])

        if latest is None:
            print("  ERROR: No current glucose data returned.")
            print("\n>>> FAILURE <<<")
            sys.exit(1)

        value = latest.value
        timestamp = latest.timestamp
        trend = latest.trend
        now = datetime.now(timezone.utc)

        # Try to calculate reading age
        reading_age_str = "unknown"
        try:
            if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo is not None:
                age = now - timestamp
            else:
                age = now - timestamp.replace(tzinfo=timezone.utc)
            age_minutes = int(age.total_seconds() / 60)
            reading_age_str = f"{age_minutes} min ago"
        except Exception:
            reading_age_str = "could not calculate"

        print(f"  Glucose: {int(value)} mg/dL")
        print(f"  Trend: {trend.name} {trend.indicator}")
        print(f"  Timestamp: {timestamp}")
        print(f"  Reading age: {reading_age_str}")
        print(f"  is_high: {latest.is_high}, is_low: {latest.is_low}")

        # Verdict
        print("\n" + "=" * 50)
        print(">>> SUCCESS <<<")
        print("=" * 50)
        print("\nThe pylibrelinkup library is working correctly.")
        print("You can proceed with the lib-based implementation.")

    except FileNotFoundError:
        print("ERROR: config.yaml not found.")
        print("Copy config.example.yaml to config.yaml and fill in your credentials.")
        print("\n>>> FAILURE <<<")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        print("\n>>> FAILURE <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Glucose Actions — Glucose Monitor & Alert System

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-31%20passing-brightgreen.svg)](#tests)

Glucose monitoring system via [LibreLinkUp](https://librelinkup.com/) with automated alerts. Reads glucose data from a FreeStyle Libre CGM sensor remotely and fires alerts when levels leave the safe range.

Built for diabetics and their caregivers who want reliable, automated glucose alerts beyond the mobile app.

> **Note:** The WhatsApp Cloud API output has been implemented but **not yet tested with a real Meta Business account**. If you set it up and test it, please [open an issue](https://github.com/rreal/glucose-actions/issues) or PR to share your experience — your feedback will help other users!

## Features

- **Automatic glucose reading** via [pylibrelinkup](https://pypi.org/project/pylibrelinkup/) (LibreLinkUp API)
- **Configurable alert thresholds** for hypo/hyper (default: < 70 and > 180 mg/dL)
- **Smart cooldown** between repeated alerts (default: 20 min), with reset on return to normal
- **Stale reading detection** (ignores readings older than 15 min)
- **Customizable alert messages** — change language and format via config file
- **Pluggable outputs:**
  - Webhook (Alexa via VoiceMonkey)
  - WhatsApp (Meta Cloud API) *(untested — contributions welcome!)*
- **State persistence** between executions (atomic JSON writes)
- **File lock** to prevent overlapping cron executions
- **Trend data** — trend arrow included in alerts (↓ ↘ → ↗ ↑)

## Architecture

```
cron (every 5 min)
  └── src/main.py (orchestrator)
        ├── src/glucose_reader.py    → pylibrelinkup → LibreLinkUp API
        ├── src/alert_engine.py      → threshold evaluation + cooldown
        ├── src/state.py             → JSON state persistence
        └── src/outputs/
              ├── base.py            → BaseOutput (ABC)
              ├── webhook.py         → Alexa/VoiceMonkey
              └── whatsapp.py        → WhatsApp Cloud API
```

## Requirements

- Python 3.12+
- Linux (uses `fcntl` for file locking)
- LibreLinkUp account with at least one shared patient connection
- (Optional) [VoiceMonkey](https://voicemonkey.io/) account for Alexa alerts
- (Optional) [Meta Business](https://business.facebook.com/) account for WhatsApp alerts

## Installation

```bash
# Clone the repository
git clone https://github.com/rreal/glucose-actions.git
cd glucose-actions

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create config with your credentials
cp config.example.yaml config.yaml
chmod 600 config.yaml
# Edit config.yaml with your values
```

## Configuration

### LibreLinkUp Credentials

In `config.yaml`:

```yaml
librelinkup:
  email: "your-email@example.com"
  password: "your-password"
```

Or via environment variables (recommended):

```bash
export LIBRELINKUP_EMAIL="your-email@example.com"
export LIBRELINKUP_PASSWORD="your-password"
```

### Alert Thresholds

```yaml
alerts:
  low_threshold: 70         # mg/dL — below this triggers hypo alert
  high_threshold: 180        # mg/dL — above this triggers hyper alert
  cooldown_minutes: 20       # minutes between repeated alerts for same level
  max_reading_age_minutes: 15  # ignore readings older than this
```

### Alert Messages (customizable)

Alert messages are fully configurable via `config.yaml`. Available placeholders: `{value}` (glucose mg/dL), `{trend}` (trend arrow), `{level}` (low/high).

```yaml
alerts:
  messages:
    # Portuguese (default)
    low: "Atencao: glicose em {value} mg/dL {trend}, nivel baixo"
    high: "Atencao: glicose em {value} mg/dL {trend}, nivel alto"

    # English example
    # low: "Warning: glucose at {value} mg/dL {trend}, level low"
    # high: "Warning: glucose at {value} mg/dL {trend}, level high"

    # Spanish example
    # low: "Atencion: glucosa en {value} mg/dL {trend}, nivel bajo"
    # high: "Atencion: glucosa en {value} mg/dL {trend}, nivel alto"
```

If no messages are configured, defaults to Portuguese.

### Output: Webhook (Alexa/VoiceMonkey)

See the full setup guide: **[VoiceMonkey Setup](docs/voicemonkey-setup.md)**

```yaml
outputs:
  - type: webhook
    enabled: true
    url: "https://api-v2.voicemonkey.io/announcement"
    token: "your-voicemonkey-token"
    device: "your-device-id"
    language: "pt-BR"      # pronunciation language (e.g. pt-BR, en-US, es-ES)
```

### Output: WhatsApp (Meta Cloud API)

> **Status:** Implemented but not yet tested with a real account. See [Contributing](CONTRIBUTING.md) if you test it.

See the full setup guide: **[WhatsApp Cloud API Setup](docs/whatsapp-setup.md)**

```yaml
outputs:
  - type: whatsapp
    enabled: true
    phone_number_id: "YOUR_PHONE_NUMBER_ID"
    access_token: ""  # or set WHATSAPP_ACCESS_TOKEN env var
    recipient: "5511999999999"
    template_name: "glucose_alert"
    language_code: "pt_BR"
```

## Running

### Step 1: Validate connections

Before running the system, validate each connection individually:

```bash
source .venv/bin/activate

# 1. Validate LibreLinkUp API connection
python validate_lib.py
# Expected: patient name, glucose value, trend, and SUCCESS

# 2. Validate Alexa/VoiceMonkey webhook (if enabled)
python validate_webhook.py
# Expected: Alexa speaks the test message and script shows SUCCESS

# 3. Validate WhatsApp Cloud API (if enabled)
python validate_whatsapp.py
# Expected: test message arrives on WhatsApp and script shows SUCCESS
```

### Step 2: Manual test run

Run the full system once to verify everything works end-to-end:

```bash
source .venv/bin/activate
python -m src.main
```

This will read the current glucose value, evaluate thresholds, and send alerts if needed. Check the output for any errors.

### Step 3: Set up cron (recommended)

Once validated, schedule automatic execution every 5 minutes:

```bash
# Edit crontab
crontab -e
```

Add one of the following lines (adjust the path to your installation):

```bash
# Basic — logs to file
*/5 * * * * cd /path/to/glucose-actions && .venv/bin/python -m src.main >> /var/log/glucose-actions.log 2>&1

# With env vars for credentials (instead of config.yaml)
*/5 * * * * cd /path/to/glucose-actions && LIBRELINKUP_EMAIL="your@email.com" LIBRELINKUP_PASSWORD="yourpass" WHATSAPP_ACCESS_TOKEN="your-token" .venv/bin/python -m src.main >> /var/log/glucose-actions.log 2>&1
```

> **Note:** The file lock mechanism prevents overlapping runs. If a previous execution is still running when cron triggers the next one, it will exit gracefully.

## Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Project Structure

```
glucose-actions/
├── config.example.yaml       # Configuration template
├── config.yaml               # Your configuration (not committed)
├── requirements.txt           # Python dependencies
├── validate_lib.py            # LibreLinkUp connection validation
├── validate_webhook.py        # Webhook (Alexa/VoiceMonkey) connection validation
├── validate_whatsapp.py       # WhatsApp Cloud API connection validation
├── docs/
│   ├── voicemonkey-setup.md   # VoiceMonkey/Alexa setup guide
│   └── whatsapp-setup.md      # WhatsApp Cloud API setup guide
├── src/
│   ├── __init__.py
│   ├── main.py                # Entry point — orchestrates read → evaluate → alert
│   ├── glucose_reader.py      # Glucose reading via pylibrelinkup
│   ├── alert_engine.py        # Threshold evaluation + cooldown + messages
│   ├── state.py               # State persistence (atomic JSON)
│   └── outputs/
│       ├── __init__.py
│       ├── base.py            # BaseOutput (ABC)
│       ├── webhook.py         # Webhook HTTP POST output
│       └── whatsapp.py        # WhatsApp Cloud API output
├── tests/
│   ├── __init__.py
│   ├── test_alert_engine.py   # Alert engine tests
│   ├── test_state.py          # State persistence tests
│   └── test_whatsapp_output.py # WhatsApp output tests
├── state.json                 # State between executions (not committed)
├── LICENSE                    # MIT License
├── CONTRIBUTING.md            # Contribution guidelines
└── .gitignore
```

## Adding New Outputs

Create a new class extending `BaseOutput`:

```python
from src.outputs.base import BaseOutput

class MyOutput(BaseOutput):
    def send_alert(self, message: str, glucose_value: int, level: str) -> bool:
        # Implement sending logic
        # Return True on success, False on failure
        ...
```

Add the type in `build_outputs()` in `src/main.py` and the configuration in `config.yaml`. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Security

- `config.yaml` contains credentials — **never commit** (protected by `.gitignore`)
- Use environment variables for secrets in production
- `chmod 600 config.yaml` to restrict access
- WhatsApp tokens are never logged (redacted in debug output)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Especially interested in:
- Testing the WhatsApp Cloud API output with a real Meta Business account
- New output plugins (Telegram, SMS, push notifications, etc.)
- Trend-based predictive alerts

## License

[MIT](LICENSE)

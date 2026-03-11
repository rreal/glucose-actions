# VoiceMonkey Setup (Alexa alerts)

[VoiceMonkey](https://voicemonkey.io/) lets you trigger Alexa text-to-speech announcements via HTTP API. When glucose levels go out of range, your Echo device will speak the alert message out loud — ideal for caregivers monitoring remotely or for nighttime alerts.

## Before you start

You will need:

- An Amazon Echo device (Echo Dot, Echo Show, etc.)
- The **Alexa app** installed on your phone
- A free [VoiceMonkey](https://voicemonkey.io/) account

## About the announcement prefix

Alexa always says something like *"[device name] says"* before speaking the alert message. For example:

> *"glucosealert says: Atencao, glicose em 55 mg/dL, nivel baixo"*

This is an **Amazon/Alexa platform limitation** that applies to all third-party announcements and cannot be disabled. After a few times you'll naturally learn to ignore the prefix and focus on the alert content.

**Tip:** Choose a short, recognizable name for your Speaker Device (e.g. "glucosealert") so the prefix stays brief.

## Step 1: Create a VoiceMonkey account

1. Go to [voicemonkey.io](https://voicemonkey.io/) and sign up
2. Link your Amazon account when prompted

## Step 2: Enable the VoiceMonkey Alexa skill

1. Open the **Alexa app** on your phone
2. Go to **More** > **Skills & Games**
3. Search for **"Voice Monkey"**
4. Tap **Enable** and link your VoiceMonkey account

## Step 3: Create a Speaker Device

There are two types of devices in VoiceMonkey. Make sure to create the correct one:

| Type | Purpose |
|------|---------|
| **Speaker Device** | Receives text and makes Alexa speak it (this is what we need) |
| Routine Trigger | Only triggers Alexa routines (does NOT speak text) |

1. In the [VoiceMonkey dashboard](https://app.voicemonkey.io/), go to **Manage Devices**
2. Create a new **Speaker Device**
3. Give it a name (e.g. "glucosealert") — this name will appear in the announcement prefix
4. Note the **Device ID** shown — you'll need it for `config.yaml`

## Step 4: Create an Alexa Routine

The Speaker Device needs an Alexa Routine to know which Echo device should speak. Without this routine, Alexa will just say *"someone is adding [device name]"* instead of speaking the actual message.

1. Open the **Alexa app** on your phone
2. Go to **More** > **Routines** > tap **+** to create a new routine
3. **When this happens (trigger):**
   - Tap **Smart Home**
   - Find and select your VoiceMonkey Speaker Device (e.g. "glucosealert")
4. **Add action:**
   - Tap **Skills**
   - Select **"Voice Monkey"**
5. **From (device):**
   - Select the Echo device that should speak the alerts (e.g. "Echo Dot de Artur")
6. Tap **Save**

> **Common mistake:** Do NOT use "Custom/Personalizado" as the action — this makes Alexa speak a fixed phrase and ignore the API text. You must select the **Voice Monkey skill** as the action.

## Step 5: Get your API token

1. In the [VoiceMonkey dashboard](https://app.voicemonkey.io/), go to **API** or **Settings**
2. Copy your **API Token**

## Step 6: Configure

Fill in your `config.yaml`:

```yaml
outputs:
  - type: webhook
    enabled: true
    url: "https://api-v2.voicemonkey.io/announcement"
    token: "your-voicemonkey-token"
    device: "your-device-id"        # the Speaker Device ID from step 3
    language: "pt-BR"               # pronunciation language (e.g. pt-BR, en-US, es-ES)
```

The `language` parameter controls Alexa's pronunciation. Use `pt-BR` for Portuguese, `en-US` for English, `es-ES` for Spanish, etc. Without this, Alexa will try to read Portuguese text with English pronunciation, making it hard to understand.

## Step 7: Test

```bash
source .venv/bin/activate

# Test with a custom message
python validate_webhook.py "Teste de conexão"

# Test with the configured alert phrases (low + high)
python validate_webhook.py
```

Your Echo device should speak the messages. If something is wrong:

| Problem | Likely cause |
|---------|-------------|
| Alexa says *"someone is adding [name]"* only | The Alexa Routine is missing or not saved correctly (redo step 4) |
| Alexa says a fixed phrase, ignoring your text | The routine action is set to "Custom" instead of the Voice Monkey skill |
| Text is spoken but pronunciation is wrong | The `language` field is missing or incorrect in `config.yaml` |
| Script shows SUCCESS but Alexa doesn't speak | Check that the routine points to the correct Echo device |
| Script shows FAILURE | Check that `token` and `device` are correct |

# VoiceMonkey Setup (Alexa alerts)

[VoiceMonkey](https://voicemonkey.io/) lets you trigger Alexa announcements via HTTP webhooks. Here's how to set it up:

> **Note:** Alexa always prefixes announcements with *"[device name] says"* before speaking the message. This is an Alexa platform limitation and cannot be disabled.

## 1. Create a VoiceMonkey account

1. Go to [voicemonkey.io](https://voicemonkey.io/) and sign up
2. Link your Amazon account when prompted

## 2. Enable the VoiceMonkey Alexa skill

1. Open the Alexa app on your phone
2. Go to **Skills & Games** and search for **Voice Monkey**
3. Enable the skill and link your VoiceMonkey account

## 3. Create a Speaker Device

1. In the [VoiceMonkey dashboard](https://app.voicemonkey.io/), go to **Manage Devices**
2. Create a new **Speaker Device** (not a Routine Trigger)
3. Give it a name (e.g. "glucosealert")
4. Note the **Device ID** — this is the `device` in your config

## 4. Create an Alexa Routine

The Speaker Device needs an Alexa Routine to deliver announcements:

1. Open the **Alexa app** on your phone
2. Go to **More** > **Routines** > **+** (create new)
3. **When (trigger):** tap "Smart Home" > select your VoiceMonkey Speaker Device
4. **Add action:** select **"Skills"** > choose **"Voice Monkey"**
5. **From:** select the Echo device that should speak (e.g. your Echo Dot)
6. Save the routine

## 5. Get your API token

1. In the VoiceMonkey dashboard, go to **API** or **Settings**
2. Copy your **API Token** — this is the `token` in your config

## 6. Configure and test

1. Fill in your `config.yaml`:

```yaml
outputs:
  - type: webhook
    enabled: true
    url: "https://api-v2.voicemonkey.io/announcement"
    token: "your-voicemonkey-token"
    device: "your-device-id"
    language: "pt-BR"      # pronunciation language (e.g. pt-BR, en-US, es-ES)
```

2. Run the validation:
   ```bash
   # Test with configured alert phrases
   python validate_webhook.py

   # Or test with a custom message
   python validate_webhook.py "Teste de conexão"
   ```
3. Your Alexa device should speak the messages in the configured language

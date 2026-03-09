# VoiceMonkey Setup (Alexa alerts)

[VoiceMonkey](https://voicemonkey.io/) lets you trigger Alexa announcements via HTTP webhooks. Here's how to set it up:

## 1. Create a VoiceMonkey account

1. Go to [voicemonkey.io](https://voicemonkey.io/) and sign up
2. Link your Amazon account when prompted

## 2. Enable the VoiceMonkey Alexa skill

1. Open the Alexa app on your phone
2. Go to **Skills & Games** and search for **Voice Monkey**
3. Enable the skill and link your VoiceMonkey account

## 3. Create a device (monkey)

1. In the [VoiceMonkey dashboard](https://app.voicemonkey.io/), go to **Manage Monkeys**
2. Click **Add a Monkey** and give it a name (e.g. "glucose-alert")
3. Select the Alexa device that should speak the alerts
4. Note the **monkey name** — this is the `device` in your config

## 4. Get your API token

1. In the VoiceMonkey dashboard, go to **API** or **Settings**
2. Copy your **API Token** — this is the `token` in your config

## 5. Configure and test

1. Fill in `url`, `token`, and `device` in your `config.yaml`:

```yaml
outputs:
  - type: webhook
    enabled: true
    url: "https://api-v2.voicemonkey.io/announcement"
    token: "your-voicemonkey-token"
    device: "your-device"
```

2. Run the validation:
   ```bash
   python validate_webhook.py
   ```
3. Your Alexa device should speak the configured alert messages

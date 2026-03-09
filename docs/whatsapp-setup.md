# WhatsApp Cloud API Setup

> **Note:** This output has been implemented but **not yet tested with a real Meta Business account**. The steps below are based on Meta's documentation. If you complete the setup, please [share your experience](https://github.com/rreal/glucose-actions/issues) to help others!

## 1. Create a Meta Business Manager account

1. Go to [business.facebook.com](https://business.facebook.com/) and create a business account (or use an existing one)
2. Go to [developers.facebook.com](https://developers.facebook.com/) and log in with the same account

## 2. Create an App in Meta for Developers

1. At [developers.facebook.com/apps](https://developers.facebook.com/apps), click **Create App**
2. Select **Other** as app type
3. Select **Business** as type
4. Name it (e.g. "Glucose Monitor") and link it to your business account
5. In the app dashboard, click **Add Product** and select **WhatsApp**

## 3. Configure phone number (sender)

> **Important:** The **sender** number (the one sending alerts) cannot be active on WhatsApp personal or WhatsApp Business app at the same time. The **recipient** number (the one receiving alerts) is your normal personal WhatsApp — no restrictions.

**Option A: Meta's test number (recommended to get started)**

Meta provides a free test number for development. This is the fastest way to test without needing an extra SIM card.

1. In the sidebar, go to **WhatsApp > API Setup**
2. The test number will already be available automatically
3. Note the **Phone Number ID** shown — this is the `phone_number_id` for your config
4. Test number limitations:
   - Can only send to registered test recipient numbers (maximum 5)
   - Messages arrive from a generic Meta number
   - Works perfectly to validate the system before investing in a dedicated number

**Option B: Your own number (for production)**

If you want a dedicated number (e.g. prepaid SIM or VoIP):

1. Click **Add phone number**
2. Use a number that is **not** registered on WhatsApp personal (or remove it first)
3. Verify the number via SMS or voice call
4. Note the **Phone Number ID** shown

## 4. Generate Access Token

**Temporary token (for testing):**
1. On the **API Setup** page, copy the generated temporary token
2. This token expires in 24h

**Permanent token (for production):**
1. Go to **App Settings > Basic** and note the App ID
2. In Meta Business Manager, go to **Settings > System Users**
3. Create a new system user as **Admin**
4. Click **Generate Token** for this user
5. Select the app and permissions: `whatsapp_business_messaging`, `whatsapp_business_management`
6. The generated token **does not expire** — store it securely
7. Set as environment variable:
   ```bash
   export WHATSAPP_ACCESS_TOKEN="your-permanent-token"
   ```

## 5. Create Message Template

Alerts are sent as template messages (Meta's requirement for proactive messages).

1. In Meta Business Manager, go to **WhatsApp > Account Manager > Message Templates**
2. Click **Create Template**
3. Configure:
   - **Category:** Utility
   - **Name:** `glucose_alert`
   - **Language:** Portuguese (BR) — or your preferred language
   - **Body:** `{{1}}`
     - This allows the system to send the full alert message as a parameter
     - Preview example: "Atencao: glicose em 65 mg/dL ↘, nivel baixo"
4. Submit for approval — typically takes minutes to 48h
5. Wait for the status to change to **Approved**

## 6. Register recipients (development mode)

While the app is in development mode:
1. On the **API Setup** page, in the **To** section, add the numbers that will receive messages
2. Each number must confirm by receiving a verification code
3. To send to any number, the app needs to be in **production mode** (requires business verification)

## 7. Enable billing

1. In Meta Business Manager, go to **Settings > WhatsApp Payment**
2. Add a payment method
3. Cost: per delivered template message (varies by country, ~$0.01-0.03 per message)
4. For glucose alerts every 5 min with 20 min cooldown, the monthly cost will be very low

## 8. Configure and test

1. Fill in your `config.yaml`:

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

2. Run the validation script:
   ```bash
   source .venv/bin/activate
   python validate_whatsapp.py
   ```

The script will:
1. Load the configuration from `config.yaml`
2. Validate that all fields are filled in
3. Send a test message via template to the configured `recipient`
4. Show `SUCCESS` if the message was sent, or `FAILURE` with debug tips

> **Tip:** Set your own number as `recipient` to receive the test message yourself.

After the WhatsApp test, validate the complete flow:

```bash
python -m src.main
```

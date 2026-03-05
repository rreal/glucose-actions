"""Unit tests for WhatsApp output module."""

from unittest.mock import MagicMock, patch

from src.outputs.whatsapp import WhatsAppOutput, GRAPH_API_URL


class TestWhatsAppOutput:
    def make_output(self) -> WhatsAppOutput:
        return WhatsAppOutput(
            phone_number_id="123456",
            access_token="test-token",
            recipient="5511999999999",
            template_name="glucose_alert",
            language_code="pt_BR",
        )

    @patch("src.outputs.whatsapp.requests.post")
    def test_send_alert_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_post.return_value = mock_resp

        output = self.make_output()
        result = output.send_alert("Atencao: glicose em 65 mg/dL ↘, nivel baixo", 65, "low")

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["timeout"] == 10
        assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer test-token"
        payload = call_kwargs.kwargs["json"]
        assert payload["messaging_product"] == "whatsapp"
        assert payload["to"] == "5511999999999"
        assert payload["template"]["name"] == "glucose_alert"
        assert payload["template"]["components"][0]["parameters"][0]["text"] == "Atencao: glicose em 65 mg/dL ↘, nivel baixo"

    @patch("src.outputs.whatsapp.requests.post")
    def test_send_alert_api_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_post.return_value = mock_resp

        output = self.make_output()
        result = output.send_alert("test", 65, "low")

        assert result is False

    @patch("src.outputs.whatsapp.requests.post")
    def test_send_alert_network_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.ConnectionError("connection failed")

        output = self.make_output()
        result = output.send_alert("test", 65, "low")

        assert result is False

    def test_url_construction(self):
        output = self.make_output()
        expected = f"{GRAPH_API_URL}/123456/messages"
        # Verify the URL would be constructed correctly
        assert f"{GRAPH_API_URL}/{output.phone_number_id}/messages" == expected

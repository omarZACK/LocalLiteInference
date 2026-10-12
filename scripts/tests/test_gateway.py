import pytest
from scripts.litellm_client import chat_completion


def test_chat_completion():
    """Test chat completion using the litellm gateway.
    Skips if the Ollama endpoint or model is not reachable.
    """
    try:
        resp = chat_completion()
    except Exception as exc:
        pytest.skip(f"Model endpoint not reachable: {exc}")

    assert isinstance(resp, dict), "Response should be a dict"
    assert "choices" in resp, "Missing 'choices' in response"
    assert len(resp["choices"]) > 0, "Expected at least one choice"
    message = resp["choices"][0]["message"]["content"]
    assert isinstance(message, str), "Message content must be a string"
    assert len(message.strip()) > 0, "Message content should not be empty"
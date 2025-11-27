import pytest
from unittest.mock import patch, MagicMock
import os

from backend.services.llm_service import LLMService, get_llm_service
from backend.config.settings import LLM_PROVIDER, OPENAI_API_KEY, GEMINI_API_KEY


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for consistent testing."""
    with patch.dict(os.environ, {
        "LLM_PROVIDER": "gemini",
        "GEMINI_API_KEY": "test_gemini_key",
        "OPENAI_API_KEY": "test_openai_key",
        "OPENAI_MODEL_NAME": "gpt-test-model",
    }):
        yield


def test_llm_service_initialization_simulation_true():
    """Test LLMService initializes correctly in simulation mode."""
    service = LLMService(use_simulation=True)
    assert service.use_simulation is True
    assert service.provider == "gemini"  # Default provider, but simulation takes precedence


def test_llm_service_initialization_simulation_false_gemini(mock_env_vars):
    """Test LLMService initializes correctly for real Gemini API calls."""
    with patch("backend.config.settings.LLM_PROVIDER", "gemini"):
        service = LLMService(use_simulation=False)
        assert service.use_simulation is False
        assert service.provider == "gemini"
        assert service.api_key == "test_gemini_key"
        # Should not initialize openai client
        assert service.client is None


def test_llm_service_initialization_simulation_false_openai(mock_env_vars):
    """Test LLMService initializes correctly for real OpenAI API calls."""
    with patch("backend.config.settings.LLM_PROVIDER", "openai"):
        with patch("openai.OpenAI") as mock_openai:
            service = LLMService(use_simulation=False)
            assert service.use_simulation is False
            assert service.provider == "openai"
            assert service.api_key == "test_openai_key"
            assert service.model_name == "gpt-test-model"
            mock_openai.assert_called_once_with(api_key="test_openai_key")
            assert service.client is not None


def test_llm_service_initialization_no_api_key_falls_back_to_simulation():
    """Test that if no API key is set, it falls back to simulation mode."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "", "OPENAI_API_KEY": ""}, clear=True):
        with patch("backend.config.settings.LLM_PROVIDER", "gemini"):
            service = LLMService(use_simulation=False)
            assert service.use_simulation is True  # Should fall back to simulation
        
        with patch("backend.config.settings.LLM_PROVIDER", "openai"):
            service = LLMService(use_simulation=False)
            assert service.use_simulation is True  # Should fall back to simulation


def test_get_llm_service_singleton():
    """Test that get_llm_service returns a singleton instance."""
    service1 = get_llm_service(use_simulation=True)
    service2 = get_llm_service(use_simulation=True)
    assert service1 is service2


@pytest.mark.parametrize("system_prompt_keyword, user_prompt, expected_substring", [
    ("ARCHITEKT", "Ziel", "SIMULATION: ARCHITEKT hat SMART-Vertrag"),
    ("ARCHITEKT", "Pfad-Chirurgie", "SIMULATION: ARCHITEKT hat Pfad korrigiert"),
    ("KURATOR", "Material", "SIMULATION: KURATOR hat Material generiert"),
    ("KURATOR", "Testfragen", "SIMULATION: KURATOR hat Testfragen generiert"),
    ("TUTOR", "Frage", "SIMULATION: TUTOR antwortet"),
    ("TUTOR", "Lücken-Diagnose", "SIMULATION: TUTOR diagnostiziert Lücke"),
    ("UNKNOWN", "random", "SIMULATION: LLM-Antwort nicht definiert"),
])
def test_simulate_response(system_prompt_keyword, user_prompt, expected_substring):
    """Test _simulate_response method for different agent roles."""
    service = LLMService(use_simulation=True)
    system_prompt = f"Du bist der {system_prompt_keyword}. Deine Aufgabe ist es..."
    response = service._simulate_response(system_prompt, user_prompt)
    assert expected_substring in response


@patch("requests.post")
def test_call_gemini_api(mock_post, mock_env_vars):
    """Test _call_gemini_api for successful response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {"parts": [{"text": "Gemini test response"}]}
        }]
    }
    mock_post.return_value = mock_response

    with patch("backend.config.settings.LLM_PROVIDER", "gemini"):
        service = LLMService(use_simulation=False)
        response = service.call("sys prompt", "user prompt", use_grounding=False)

        assert response == "Gemini test response"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=test_gemini_key" in args[0]
        assert "contents" in kwargs["json"]


@patch("requests.post")
def test_call_gemini_api_with_grounding(mock_post, mock_env_vars):
    """Test _call_gemini_api with grounding enabled."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {"parts": [{"text": "Gemini grounded response"}]}
        }]
    }
    mock_post.return_value = mock_response

    with patch("backend.config.settings.LLM_PROVIDER", "gemini"):
        service = LLMService(use_simulation=False)
        service.call("sys prompt", "user prompt", use_grounding=True)

        args, kwargs = mock_post.call_args
        assert "tools" in kwargs["json"]
        assert kwargs["json"]["tools"] == [{"googleSearch": {}}]


@patch("openai.OpenAI")
def test_call_openai_api(mock_openai_class, mock_env_vars):
    """Test _call_openai_api for successful response."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    mock_chat_completion = MagicMock()
    mock_chat_completion.choices[0].message.content = "OpenAI test response"
    mock_client.chat.completions.create.return_value = mock_chat_completion

    with patch("backend.config.settings.LLM_PROVIDER", "openai"):
        service = LLMService(use_simulation=False)
        response = service.call("sys prompt", "user prompt")

        assert response == "OpenAI test response"
        mock_openai_class.assert_called_once_with(api_key="test_openai_key")
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-test-model",
            messages=[
                {"role": "system", "content": "sys prompt"},
                {"role": "user", "content": "user prompt"},
            ],
            temperature=0.7,
            max_tokens=2048,
        )


@patch("openai.OpenAI")
def test_call_openai_api_error(mock_openai_class, mock_env_vars):
    """Test _call_openai_api handles API errors."""
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.side_effect = openai.APIError("Test API Error", None, None)

    with patch("backend.config.settings.LLM_PROVIDER", "openai"):
        service = LLMService(use_simulation=False)
        with pytest.raises(Exception, match="LLM API call failed: Test API Error"):
            service.call("sys prompt", "user prompt")


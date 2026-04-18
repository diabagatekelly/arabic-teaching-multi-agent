"""Tests for HuggingFace model loader."""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.models.hf_model_loader import (
    load_grading_model,
    load_teaching_model,
)


@pytest.fixture
def mock_env_with_token(monkeypatch):
    """Set HF_TOKEN in environment."""
    monkeypatch.setenv("HF_TOKEN", "hf_test_token_123")


@pytest.fixture
def mock_adapter_config():
    """Mock adapter config JSON."""
    return {"base_model_name_or_path": "unsloth/qwen2.5-7b-instruct-unsloth-bnb-4bit"}


class TestLoadTeachingModelHub:
    """Tests for load_teaching_model with HuggingFace Hub."""

    @patch("src.models.hf_model_loader.AutoTokenizer")
    @patch("src.models.hf_model_loader.AutoModelForCausalLM")
    @patch("src.models.hf_model_loader.PeftModel")
    @patch("huggingface_hub.hf_hub_download")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_from_hub_success(
        self,
        mock_file,
        mock_hub_download,
        mock_peft,
        mock_model_class,
        mock_tokenizer_class,
        mock_env_with_token,
        mock_adapter_config,
    ):
        """Should load teaching model from HuggingFace Hub with token."""
        # Setup mocks
        mock_tokenizer = MagicMock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

        mock_base_model = MagicMock()
        mock_model_class.from_pretrained.return_value = mock_base_model

        mock_model = MagicMock()
        mock_peft.from_pretrained.return_value = mock_model

        # Mock adapter config download
        mock_hub_download.return_value = "/tmp/adapter_config.json"
        mock_file.return_value.read.return_value = json.dumps(mock_adapter_config)

        # Call
        model, tokenizer = load_teaching_model(use_hub=True)

        # Assert tokenizer loaded with token
        mock_tokenizer_class.from_pretrained.assert_called_once_with(
            "kdiabagate/qwen-7b-arabic-teaching",
            trust_remote_code=True,
            token="hf_test_token_123",
        )

        # Assert base model loaded with token
        mock_model_class.from_pretrained.assert_called_once_with(
            "unsloth/qwen2.5-7b-instruct-unsloth-bnb-4bit",
            device_map="auto",
            trust_remote_code=True,
            token="hf_test_token_123",
        )

        # Assert LoRA adapter loaded with token
        mock_peft.from_pretrained.assert_called_once_with(
            mock_base_model,
            "kdiabagate/qwen-7b-arabic-teaching",
            device_map="auto",
            token="hf_test_token_123",
        )

        # Assert return values
        assert model == mock_model
        assert tokenizer == mock_tokenizer

    @patch("src.models.hf_model_loader.AutoTokenizer")
    def test_load_from_hub_no_token_warning(self, mock_tokenizer_class):
        """Should load without token if HF_TOKEN not set (warning case)."""
        # No HF_TOKEN in env
        with patch.dict("os.environ", {}, clear=True):
            with patch("src.models.hf_model_loader.AutoModelForCausalLM"):
                with patch("src.models.hf_model_loader.PeftModel"):
                    with patch("src.models.hf_model_loader.hf_hub_download"):
                        with patch(
                            "builtins.open",
                            mock_open(read_data='{"base_model_name_or_path": "test"}'),
                        ):  # noqa: E501
                            # Should not raise, just pass None as token
                            load_teaching_model(use_hub=True)

                            # Token should be None
                            call_kwargs = mock_tokenizer_class.from_pretrained.call_args[1]
                            assert call_kwargs["token"] is None


class TestLoadTeachingModelLocal:
    """Tests for load_teaching_model with local path."""

    @patch("src.models.hf_model_loader.AutoTokenizer")
    @patch("src.models.hf_model_loader.AutoModelForCausalLM")
    @patch("src.models.hf_model_loader.PeftModel")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_from_local_path_exists(
        self,
        mock_file,
        mock_peft,
        mock_model_class,
        mock_tokenizer_class,
        mock_env_with_token,
        mock_adapter_config,
    ):
        """Should load from local path if exists."""
        with patch("pathlib.Path.exists", return_value=True):
            # Setup mocks
            mock_file.return_value.read.return_value = json.dumps(mock_adapter_config)

            mock_tokenizer = MagicMock()
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

            mock_base_model = MagicMock()
            mock_model_class.from_pretrained.return_value = mock_base_model

            mock_model = MagicMock()
            mock_peft.from_pretrained.return_value = mock_model

            # Call
            model, tokenizer = load_teaching_model(use_hub=False)

            # Should use local path
            assert "models/qwen-7b-arabic-teaching" in str(
                mock_tokenizer_class.from_pretrained.call_args[0][0]
            )
            assert model == mock_model
            assert tokenizer == mock_tokenizer

    def test_load_from_local_path_not_found(self):
        """Should raise FileNotFoundError if local path doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="Teaching model not found"):
                load_teaching_model(use_hub=False)


class TestLoadGradingModelHub:
    """Tests for load_grading_model with HuggingFace Hub."""

    @patch("src.models.hf_model_loader.AutoTokenizer")
    @patch("src.models.hf_model_loader.AutoModelForCausalLM")
    @patch("src.models.hf_model_loader.PeftModel")
    @patch("huggingface_hub.hf_hub_download")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_from_hub_success(
        self,
        mock_file,
        mock_hub_download,
        mock_peft,
        mock_model_class,
        mock_tokenizer_class,
        mock_env_with_token,
        mock_adapter_config,
    ):
        """Should load grading model from HuggingFace Hub with token."""
        # Setup mocks
        mock_tokenizer = MagicMock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer

        mock_base_model = MagicMock()
        mock_model_class.from_pretrained.return_value = mock_base_model

        mock_model = MagicMock()
        mock_peft.from_pretrained.return_value = mock_model

        # Mock adapter config download
        mock_hub_download.return_value = "/tmp/adapter_config.json"
        mock_file.return_value.read.return_value = json.dumps(mock_adapter_config)

        # Call
        model, tokenizer = load_grading_model(use_hub=True)

        # Assert tokenizer loaded with token
        mock_tokenizer_class.from_pretrained.assert_called_once_with(
            "kdiabagate/qwen-7b-arabic-grading",
            trust_remote_code=True,
            token="hf_test_token_123",
        )

        # Assert base model loaded with token
        mock_model_class.from_pretrained.assert_called_once_with(
            "unsloth/qwen2.5-7b-instruct-unsloth-bnb-4bit",
            device_map="auto",
            trust_remote_code=True,
            token="hf_test_token_123",
        )

        # Assert LoRA adapter loaded with token
        mock_peft.from_pretrained.assert_called_once_with(
            mock_base_model,
            "kdiabagate/qwen-7b-arabic-grading",
            device_map="auto",
            token="hf_test_token_123",
        )

        assert model == mock_model
        assert tokenizer == mock_tokenizer


class TestLoadGradingModelLocal:
    """Tests for load_grading_model with local path."""

    def test_load_from_local_path_not_found(self):
        """Should raise FileNotFoundError if local grading model doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="Grading model not found"):
                load_grading_model(use_hub=False)


class TestErrorHandling:
    """Tests for error handling in model loading."""

    @patch("src.models.hf_model_loader.AutoTokenizer")
    def test_tokenizer_loading_error(self, mock_tokenizer_class, mock_env_with_token):
        """Should raise RuntimeError if tokenizer loading fails."""
        mock_tokenizer_class.from_pretrained.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to load teaching model"):
            load_teaching_model(use_hub=True)

    @patch("src.models.hf_model_loader.AutoTokenizer")
    @patch("src.models.hf_model_loader.AutoModelForCausalLM")
    @patch("huggingface_hub.hf_hub_download")
    def test_base_model_loading_error(
        self, mock_hub_download, mock_model_class, mock_tokenizer_class, mock_env_with_token
    ):
        """Should raise RuntimeError if base model loading fails."""
        mock_tokenizer_class.from_pretrained.return_value = MagicMock()
        mock_hub_download.return_value = "/tmp/config.json"

        with patch("builtins.open", mock_open(read_data='{"base_model_name_or_path": "test"}')):
            mock_model_class.from_pretrained.side_effect = Exception("CUDA OOM")

            with pytest.raises(RuntimeError, match="Failed to load teaching model"):
                load_teaching_model(use_hub=True)

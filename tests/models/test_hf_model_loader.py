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


class TestSharedFinetunedLoader:
    """Tests for _load_finetuned_model shared implementation."""

    @patch("src.models.hf_model_loader.AutoTokenizer")
    @patch("src.models.hf_model_loader.AutoModelForCausalLM")
    @patch("src.models.hf_model_loader.PeftModel")
    @patch("huggingface_hub.hf_hub_download")
    @patch("builtins.open", new_callable=mock_open)
    def test_hub_loading_with_token_authentication(
        self,
        mock_file,
        mock_hub_download,
        mock_peft,
        mock_model_class,
        mock_tokenizer_class,
        mock_env_with_token,
        mock_adapter_config,
    ):
        """Test Hub loading with HF token authentication through shared loader."""
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

        # Call via teaching model
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
    def test_hub_loading_without_token(self, mock_tokenizer_class):
        """Test Hub loading passes None when HF_TOKEN not set."""
        # No HF_TOKEN in env
        with patch.dict("os.environ", {}, clear=True):
            with patch("src.models.hf_model_loader.AutoModelForCausalLM"):
                with patch("src.models.hf_model_loader.PeftModel"):
                    with patch("src.models.hf_model_loader.hf_hub_download"):
                        with patch(
                            "builtins.open",
                            mock_open(read_data='{"base_model_name_or_path": "test"}'),
                        ):
                            load_teaching_model(use_hub=True)

                            # Token should be None
                            call_kwargs = mock_tokenizer_class.from_pretrained.call_args[1]
                            assert call_kwargs["token"] is None

    @patch("src.models.hf_model_loader.AutoTokenizer")
    @patch("src.models.hf_model_loader.AutoModelForCausalLM")
    @patch("src.models.hf_model_loader.PeftModel")
    @patch("builtins.open", new_callable=mock_open)
    def test_local_loading_when_path_exists(
        self,
        mock_file,
        mock_peft,
        mock_model_class,
        mock_tokenizer_class,
        mock_env_with_token,
        mock_adapter_config,
    ):
        """Test local filesystem loading when model directory exists."""
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

    def test_local_loading_raises_when_path_not_found(self):
        """Test FileNotFoundError when local model directory doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="Teaching model not found"):
                load_teaching_model(use_hub=False)


class TestLoadTeachingModel:
    """Tests specific to teaching model wrapper."""

    def test_uses_correct_hub_path_constant(self):
        """Verify teaching model uses correct HuggingFace Hub path."""
        with patch("src.models.hf_model_loader._load_finetuned_model") as mock_load:
            mock_load.return_value = (MagicMock(), MagicMock())
            load_teaching_model(use_hub=True)

            mock_load.assert_called_once_with(
                model_type="teaching",
                hf_path="kdiabagate/qwen-7b-arabic-teaching",
                local_path="models/qwen-7b-arabic-teaching",
                use_hub=True,
            )

    def test_uses_correct_local_path_constant(self):
        """Verify teaching model uses correct local filesystem path."""
        with patch("src.models.hf_model_loader._load_finetuned_model") as mock_load:
            mock_load.return_value = (MagicMock(), MagicMock())
            load_teaching_model(use_hub=False)

            call_kwargs = mock_load.call_args[1]
            assert call_kwargs["local_path"] == "models/qwen-7b-arabic-teaching"
            assert call_kwargs["use_hub"] is False


class TestLoadGradingModel:
    """Tests specific to grading model wrapper."""

    def test_uses_correct_hub_path_constant(self):
        """Verify grading model uses correct HuggingFace Hub path."""
        with patch("src.models.hf_model_loader._load_finetuned_model") as mock_load:
            mock_load.return_value = (MagicMock(), MagicMock())
            load_grading_model(use_hub=True)

            mock_load.assert_called_once_with(
                model_type="grading",
                hf_path="kdiabagate/qwen-7b-arabic-grading",
                local_path="models/qwen-7b-arabic-grading",
                use_hub=True,
            )

    def test_uses_correct_local_path_constant(self):
        """Verify grading model uses correct local filesystem path."""
        with patch("src.models.hf_model_loader._load_finetuned_model") as mock_load:
            mock_load.return_value = (MagicMock(), MagicMock())
            load_grading_model(use_hub=False)

            call_kwargs = mock_load.call_args[1]
            assert call_kwargs["local_path"] == "models/qwen-7b-arabic-grading"
            assert call_kwargs["use_hub"] is False

    def test_raises_when_local_path_not_found(self):
        """Test FileNotFoundError for missing grading model directory."""
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

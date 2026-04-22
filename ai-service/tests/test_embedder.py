"""Tests for embedder — provider abstraction, Ollama vs Azure OpenAI."""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.services.embedder import get_embedding


class TestGetEmbedding:
    """Interview topic: provider abstraction, embedding pipeline."""

    @pytest.mark.asyncio
    async def test_ollama_provider(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.embedder.settings") as mock_settings:
            mock_settings.EMBEDDING_PROVIDER = "ollama"
            mock_settings.OLLAMA_BASE_URL = "http://ollama:11434"
            mock_settings.EMBED_MODEL = "nomic-embed-text"

            with patch("app.services.embedder.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                embedding = await get_embedding("organic apples")

        assert embedding == [0.1, 0.2, 0.3]
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        assert "nomic-embed-text" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_azure_provider(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [{"embedding": [0.4, 0.5, 0.6]}]}
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.embedder.settings") as mock_settings:
            mock_settings.EMBEDDING_PROVIDER = "azure_openai"
            mock_settings.AZURE_OPENAI_ENDPOINT = "https://myoai.openai.azure.com"
            mock_settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
            mock_settings.AZURE_OPENAI_API_KEY = "test-key"

            with patch("app.services.embedder.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                embedding = await get_embedding("organic apples")

        assert embedding == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_returns_list_of_floats(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"embedding": [0.1] * 768}
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.embedder.settings") as mock_settings:
            mock_settings.EMBEDDING_PROVIDER = "ollama"
            mock_settings.OLLAMA_BASE_URL = "http://ollama:11434"
            mock_settings.EMBED_MODEL = "nomic-embed-text"

            with patch("app.services.embedder.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client_cls.return_value = mock_client

                embedding = await get_embedding("test")

        assert len(embedding) == 768
        assert all(isinstance(v, float) for v in embedding)

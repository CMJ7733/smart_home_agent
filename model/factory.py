import os
from abc import ABC, abstractmethod
from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.core.config import get_settings


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | ChatOllama]:
        raise NotImplementedError


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> ChatOllama:
        settings = get_settings()
        return ChatOllama(
            model=os.environ.get("OLLAMA_CHAT_MODEL", settings.chat_model_name),
            base_url=os.environ.get("OLLAMA_BASE_URL", settings.ollama_base_url),
            temperature=0.3,
        )


class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> OllamaEmbeddings:
        settings = get_settings()
        return OllamaEmbeddings(
            model=os.environ.get("OLLAMA_EMBEDDING_MODEL", settings.embedding_model_name),
            base_url=os.environ.get("OLLAMA_BASE_URL", settings.ollama_base_url),
        )


chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()

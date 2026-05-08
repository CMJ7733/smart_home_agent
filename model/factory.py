import os
from abc import ABC, abstractmethod
from typing import Optional, Union

from langchain_core.embeddings import Embeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.core.config import get_settings


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Union[Embeddings, ChatOllama]]:
        raise NotImplementedError


class ChatModelFactory(BaseModelFactory):
    def generator(self):
        settings = get_settings()
        provider = os.environ.get("LLM_PROVIDER", settings.llm_provider)

        if provider == "api":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=os.environ.get("API_MODEL_NAME", settings.api_model_name),
                api_key=os.environ.get("API_KEY", settings.api_key),
                base_url=os.environ.get("API_BASE_URL", settings.api_base_url),
                temperature=0.3,
                max_tokens=2048,
            )

        return ChatOllama(
            model=os.environ.get("OLLAMA_CHAT_MODEL", settings.chat_model_name),
            base_url=os.environ.get("OLLAMA_BASE_URL", settings.ollama_base_url),
            temperature=0.3,
            num_ctx=4096,
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

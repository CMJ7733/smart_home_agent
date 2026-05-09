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
        provider = settings.llm_provider

        if provider == "api":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=settings.api_model_name,
                api_key=settings.api_key,
                base_url=settings.api_base_url,
                temperature=0.3,
                max_tokens=20480,
            )

        return ChatOllama(
            model=settings.chat_model_name,
            base_url=settings.ollama_base_url,
            temperature=0.3,
            num_ctx=4096,
        )


class EmbeddingsFactory(BaseModelFactory):
    def generator(self):
        settings = get_settings()
        embed_provider = settings.embed_provider

        if embed_provider == "api":
            from langchain_openai import OpenAIEmbeddings
            embed_api_key = settings.embed_api_key or settings.api_key
            embed_base_url = settings.embed_api_base_url or None
            return OpenAIEmbeddings(
                model=settings.embed_model_name,
                api_key=embed_api_key,
                base_url=embed_base_url,
                chunk_size=64,
            )

        return OllamaEmbeddings(
            model=os.environ.get("OLLAMA_EMBEDDING_MODEL", settings.embedding_model_name),
            base_url=os.environ.get("OLLAMA_BASE_URL", settings.ollama_base_url),
        )


chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()

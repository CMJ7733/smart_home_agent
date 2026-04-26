from abc import ABC, abstractmethod
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_ollama import ChatOllama
from utils.config_handler import rag_conf


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self) -> Optional[Embeddings | ChatOllama]:
        pass


class ChatModelFactory(BaseModelFactory):
    def generator(self) -> ChatOllama:
        return ChatOllama(
            model="gemma4:e4b",          
            base_url="http://localhost:11434",
            temperature=0.1,                 
        )


class EmbeddingsFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings]:
        return DashScopeEmbeddings(model=rag_conf["embedding_model_name"])


chat_model = ChatModelFactory().generator()
embed_model = EmbeddingsFactory().generator()

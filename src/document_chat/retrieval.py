import sys
import os
from operator import itemgetter
from typing import List, Optional, Dict, Any

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from utils.model_loader import ModelLoader
from utils.token_counter import create_token_callback, get_token_counter
from exception.custom_exception import DocumentPortalException
from logger import GLOBAL_LOGGER as log
from prompt.prompt_library import PROMPT_REGISTRY
from model.models import PromptType


class ConversationalRAG:
    """
    LCEL-based Conversational RAG with lazy retriever initialization.

    Usage:
        rag = ConversationalRAG(session_id="abc")
        rag.load_retriever_from_qdrant(collection_name="abc", k=5)
        answer = rag.invoke("What is ...?", chat_history=[])
    """

    def __init__(self, session_id: Optional[str], retriever=None):
        try:
            self.session_id = session_id

            # Load LLM and prompts once
            self.llm = self._load_llm()
            self.contextualize_prompt: ChatPromptTemplate = PROMPT_REGISTRY[
                PromptType.CONTEXTUALIZE_QUESTION.value
            ]
            self.qa_prompt: ChatPromptTemplate = PROMPT_REGISTRY[
                PromptType.CONTEXT_QA.value
            ]

            # Lazy pieces
            self.retriever = retriever
            self.chain = None
            if self.retriever is not None:
                self._build_lcel_chain()

            log.info("ConversationalRAG initialized", session_id=self.session_id)
        except Exception as e:
            log.error("Failed to initialize ConversationalRAG", error=str(e))
            raise DocumentPortalException("Initialization error in ConversationalRAG", sys)

    # ---------- Public API ----------

    def load_retriever_from_qdrant(
        self,
        collection_name: str,
        k: int = 5,
        search_type: str = "similarity",
        search_kwargs: Optional[Dict[str, Any]] = None,
    ):
        """
        Load Qdrant vectorstore and build retriever + LCEL chain.
        """
        try:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
            client = QdrantClient(url=qdrant_url)
            if not client.collection_exists(collection_name):
                raise FileNotFoundError(f"Qdrant collection not found: {collection_name}")

            embeddings = ModelLoader().load_embeddings()
            vectorstore = QdrantVectorStore(client=client, collection_name=collection_name, embedding=embeddings)

            self.retriever = vectorstore.as_retriever(
                search_type=search_type, search_kwargs=search_kwargs or {"k": k}
            )
            self._build_lcel_chain()

            log.info(
                "Qdrant retriever loaded successfully",
                collection_name=collection_name,
                k=k,
                session_id=self.session_id,
            )
            return self.retriever

        except Exception as e:
            log.error("Failed to load retriever from Qdrant", error=str(e))
            raise DocumentPortalException("Loading error in ConversationalRAG", sys)

    def invoke(self, user_input: str, chat_history: Optional[List[BaseMessage]] = None) -> Dict[str, Any]:
        """
        Invoke the LCEL pipeline.

        Returns:
            Dict containing 'answer' and 'token_usage' for the operation.
        """
        try:
            if self.chain is None:
                raise DocumentPortalException(
                    "RAG chain not initialized. Call load_retriever_from_qdrant() before invoke().", sys
                )
            chat_history = chat_history or []
            payload = {"input": user_input, "chat_history": chat_history}

            # Create token counter callback for this invocation
            token_callback = create_token_callback(
                operation_type="chat",
                session_id=self.session_id
            )

            # Get usage before invocation
            counter = get_token_counter()
            usage_before = counter.get_usage_by_type("chat")

            answer = self.chain.invoke(payload, config={"callbacks": [token_callback]})

            # Calculate tokens used in this call
            usage_after = counter.get_usage_by_type("chat")
            tokens_used = {
                "input_tokens": usage_after["input_tokens"] - usage_before["input_tokens"],
                "output_tokens": usage_after["output_tokens"] - usage_before["output_tokens"],
                "total_tokens": usage_after["total_tokens"] - usage_before["total_tokens"]
            }

            if not answer:
                log.warning(
                    "No answer generated", user_input=user_input, session_id=self.session_id
                )
                return {"answer": "no answer generated.", "token_usage": tokens_used}
            log.info(
                "Chain invoked successfully",
                session_id=self.session_id,
                user_input=user_input,
                answer_preview=str(answer)[:150],
                token_usage=tokens_used
            )
            return {"answer": answer, "token_usage": tokens_used}
        except Exception as e:
            log.error("Failed to invoke ConversationalRAG", error=str(e))
            raise DocumentPortalException("Invocation error in ConversationalRAG", sys)

    # ---------- Internals ----------

    def _load_llm(self):
        try:
            # 1. Determine Primary and Backup Providers using simple logic
            #    (In a real app, this map could be in config.yaml)
            default_provider = os.getenv("LLM_PROVIDER", "groq")
            backup_provider = "google" if default_provider == "groq" else "groq"

            loader = ModelLoader()
            
            # 2. Load Primary
            log.info("Loading Primary LLM", provider=default_provider)
            primary_llm = loader.load_llm(provider=default_provider)
            if not primary_llm:
                 raise ValueError("Primary LLM could not be loaded")

            # 3. Load Backup (Best Effort)
            try:
                log.info("Loading Backup LLM", provider=backup_provider)
                backup_llm = loader.load_llm(provider=backup_provider)
            except Exception as e:
                log.warning("Failed to load Backup LLM. Fallback will not be active.", error=str(e))
                backup_llm = None

            # 4. Wrap with Fallback if possible
            if backup_llm:
                log.info("LLM Fallback configured", primary=default_provider, backup=backup_provider)
                # This returns a RunnableWithFallbacks
                return primary_llm.with_fallbacks([backup_llm])
            else:
                log.info("LLM loaded (No Fallback)", provider=default_provider)
                return primary_llm

        except Exception as e:
            log.error("Failed to load LLM", error=str(e))
            raise DocumentPortalException("LLM loading error in ConversationalRAG", sys)

    @staticmethod
    def _format_docs(docs) -> str:
        return "\n\n".join(getattr(d, "page_content", str(d)) for d in docs)

    def _build_lcel_chain(self):
        try:
            if self.retriever is None:
                raise DocumentPortalException("No retriever set before building chain", sys)

            # 1) Rewrite user question with chat history context
            question_rewriter = (
                {"input": itemgetter("input"), "chat_history": itemgetter("chat_history")}
                | self.contextualize_prompt
                | self.llm
                | StrOutputParser()
            )

            # 2) Retrieve docs for rewritten question
            retrieve_docs = question_rewriter | self.retriever | self._format_docs

            # 3) Answer using retrieved context + original input + chat history
            self.chain = (
                {
                    "context": retrieve_docs,
                    "input": itemgetter("input"),
                    "chat_history": itemgetter("chat_history"),
                }
                | self.qa_prompt
                | self.llm
                | StrOutputParser()
            )

            log.info("LCEL graph built successfully", session_id=self.session_id)
        except Exception as e:
            log.error("Failed to build LCEL chain", error=str(e), session_id=self.session_id)
            raise DocumentPortalException("Failed to build LCEL chain", sys)
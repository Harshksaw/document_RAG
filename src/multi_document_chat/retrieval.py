
import sys
import os
from operator import itemgetter


from prompt.prompt_library import PROMPT_REGISTRY
from models.model import PromptType
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from utils.model_loader import ModelLoader
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.memory import InMemoryChatMessageHistory
from langchain_core.runnables import Runnables 







class ConversationalRAG():

    def __init__(self,session_id:str, retriever=None):

        try:
            self.log = CustomLogger().get_logger(__name__)
            self.session_id = session_id
            self.retriever = retriever

            self.log.info("ConversationalRAG initialized", session_id = self.session_id)

            self.llm = self._load_llm()
            self.contextualize_prompt:ChatPromptTemplate = PROMPT_REGISTRY.get(PromptType.CONTEXTUALIZE_QUESTION.value)
            self.qa_prompt: ChatPromptTemplate = PROMPT_REGISTRY.get(PromptType.QA.value)

            if retriever is None:
                self.retriever = self.load_retriever_from_faiss()
            else:
                self.retriever = retriever
            self.retriever = retriever
            self._build_lcel_chain()
            self.log.info("ConversationalRAG initialized", session_id = self.session_id)




        except Exception as e:
            self.log.error(f"Failed to initialize ConversationalRAG: {str(e)}")
            raise DocumentPortalException(f"Failed to initialize ConversationalRAG: {str(e)}")
        

    def load_retriever_from_faiss(self):
        """Load retriever from faiss index"""
        try:
            embeddings = ModelLoader().load_embeddings()
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"Faiss index directory does not exist: {index_path}")


            vectorstore = FAISS.load_local(
                index_path,
                embeddings
                allow_dangerous_deserialization=True
            )

            self.retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
            self.log.info("Retriever loaded successfully", session_id = self.session_id)

            self._build_lcel_chain()
            self.log.info("LCEL chain built successfully", session_id = self.session_id)

            return self.retriever
                
      
        except Exception as e:
            self.log.error(f"Failed to load retriever from faiss index: {str(e)}")
            raise DocumentPortalException(f"Failed to load retriever from faiss index: {str(e)}")

    def invoke(self):
        """Invoke the ConversationalRAG"""
        try:
            

        except Exception as e:
            self.log.error(f"Failed to invoke ConversationalRAG: {str(e)}")
            raise DocumentPortalException(f"Failed to invoke ConversationalRAG: {str(e)}")


    def _load_llm(self):
        try:
            llm = ModelLoader().load_llm()
            if not llm:
                raise DocumentPortalException("LLM not loaded")
            self.log.info("LLM loaded successfully", session_id = self.session_id)
            return llm
        except Exception as e:
            self.log.error(f"Failed to load LLM: {str(e)}")
            raise DocumentPortalException(f"Failed to load LLM: {str(e)}")


    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)


    def _build_lcel_chain(self):
        try:
            question_rewriter = (
                {"input": itemgetter("input"), "chat_history": itemgetter("chat_history")}
                | 
                self.contextualize_prompt
                | 
                self.llm
                | 
                StrOutputParser()
            )

            retrieve_docs = question_rewriter | self.retriever | self._format_docs

            self.chain = (
                {
                    "context": retrieve_docs,
                    "input": itemgetter("input"),
                    "chat_history": itemgetter("chat_history"),

                }
                | 
                self.qa_prompt
                | 
                self.llm
                | 
                StrOutputParser()
            )
            self.log.info("LCEL chain built successfully", session_id = self.session_id)
            return self.chain


        except Exception as e:
            self.log.error(f"Failed to build LCEL chain: {str(e)}")
            raise DocumentPortalException(f"Failed to build LCEL chain: {str(e)}")
    
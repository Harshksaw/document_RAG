from prompt.prompt_library import PROMPT_REGISTRY
from model.models import PromptType
from logger import GLOBAL_LOGGER as log
from exception.custom_exception import DocumentPortalException
from utils.model_loader import ModelLoader
from langchain.chains import create_history_aware_retriever, create_stuff_documents_chain, create_retrieval_chain
from langchain.memory import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory


class ConversationalRAG:
    def __init__(self, session_id: str, retriever)-> None:
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.session_id = session_id
            self.retriever = retriever

            self.llm = self._load_llm()
            self.contextualize_prompt = PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt = PROMPT_REGISTRY[PromptType.QA.value]
            self.history_aware_retriever = create_history_aware_retriever(
                self.llm , self.retriever, self.contextualize_prompt
            )

            self.qa_chain = create_stuff_documents_chain(
                self.llm, self.qa_prompt
            )
            self.rag_chain = create_retrieval_chain(
                self.history_aware_retriever,
                 self.qa_chain
            )
            self.chain = RunnableWithMessageHistory(
                self.rag_chain,
                self._get_session_history(self.session_id)
                input_message_key="input",
                history_messages_key="chat_history",
                output_message_key="answer"
            )
            self.log.info("ConversationalRAG initialized successfully", session_id=self.session_id)


        except Exception as e:
            self.log.error("Error in ConversationalRAG initialization: %s", error=str(e))
            raise DocumentPortalException("Error in ConversationalRAG initialization: %s" sys)  

    def _load_llm(self)-> None:
        try:
            self.log.info("Loading LLM")
            self.llm = ModelLoader().load_llm()


            self.log.info("LLM loaded successfully")

            return self.llm
        except Exception as e:
            self.log.error("Error in loading LLM: %s", error=str(e))
            raise DocumentPortalException("Error in loading LLM: %s" sys)  


    def load_retriever(self):
        try:

            embeddings = ModelLoader().load_embeddings()
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"Index directory {index_path} does not exist")

            vectorstore = FAISS.load_local(index_path, embeddings)
            self.log.info("Vectorstore loaded successfully")

            return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})

        except Exception as e:
            self.log.error("Error in loading retriever: %s", error=str(e))
            raise DocumentPortalException("Error in loading retriever: %s" sys)  
    def invoke(self):
        try:
            self.chain.invoke({
                "input":user_input
            },
            config={
                "configurable":{"session_id":self.session_id}
            }
                )
            answer = response.get("answer", "No answer.")
            self.log.info("Answer retrieved successfully",session_id=self.session_id,user_input=user_input, answer=answer)
            return answer


        except Exception as e:
            self.log.error("Error in invoke: %s", error=str(e))
            raise DocumentPortalException("Error in invoke: %s" sys)  

    def _get_session_history(self, session_id: str):
        try:
            self.log.info("Getting session history")
            session_history = self.session_history.get(session_id, [])
            self.log.info("Session history retrieved successfully")
            return session_history
        except Exception as e:
            self.log.error("Error in getting session history: %s", error=str(e))
            raise DocumentPortalException("Error in getting session history: %s" sys)  

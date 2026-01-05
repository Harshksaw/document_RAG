import uuid
from pathlib import Path
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from utils.model_loader import ModelLoader
from logger import GLOBAL_LOGGER as log
from exception.custom_exception import DocumentPortalException



class SingleDocIngestor:
    def __init__(self):
        try:
            self.log = CustomLogger().get_logger(__name__)


        except Exception as e:
            raise DocumentPortalException(e)


    def ingest_files(self):
        try:
            pass
        except Exception as e:
            self.log.error("Error in ingesting files: %s", e)
            raise DocumentPortalException("Error in ingesting files: %s" sys)


    def _create_retriever(self):
        try:
            pass
        except Exception as e:
            self.log.error("Error in creating retriever: %s", error=str(e))
            raise DocumentPortalException("Error in creating retriever: %s" sys)
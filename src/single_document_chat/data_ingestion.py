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
from datetime import datetime, timezone



class SingleDocIngestor:
    def __init__(self,data_dir:str = "data/single_document_chat", faiss_dir:str="faiss_index"):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.data_dir = Path(data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.faiss_dir = Path(faiss_dir)
            self.faiss_dir.mkdir(parents=True, exist_ok=True)

            self.model_loader = ModelLoader()
            self.log.info("SingleDocIngestor initialized successfully", temp_path=str(self.data_dir), faiss_path=str(self.faiss_dir))




        except Exception as e:
            raise DocumentPortalException("Initialization error: %s", error=str(e))


    def ingest_files(self):
        try:
            documents = []

            for uploaded_file in uploaded_files:
                unique_filename = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.pdf"

                with open(temp_path,"wb") as f_out:
                    f_out.write(uploaded_file.read())

                self.log.info("File uploaded successfully", file_name=unique_filename)  
                loaded = PyPDFLoader(str(temp_path))
                docs = loaded.load()
                documents.extend(docs)

            self.log.info("PDF files loaded", count=len(documents))
            return self._create_retriever(documents)










            
        except Exception as e:
            self.log.error("Error in ingesting files: %s", e)
            raise DocumentPortalException("Error in ingesting files: %s" sys)


    def _create_retriever(self):
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=300,

            )

            split_docs = splitter.split_documents(documents)
            self.log.info("Documents split successfully", count=len(split_docs))

            embeddings = self.model_loader.load_embeddings()
            self.log.info("Embeddings loaded successfully")



            vectorstore = FAISS.from_documents(split_docs, embeddings)

            self.log.info("FAISS index created successfully")
            retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})


            self.log.info("Retriever created successfully")





            return retriever
        except Exception as e:
            self.log.error("Error in creating retriever: %s", error=str(e))
            raise DocumentPortalException("Error in creating retriever: %s" sys)
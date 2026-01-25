import uuid
from datetime import datetime, timezone
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from logger.custom_logger import CustomLogger

from langchain.vectorstores import FAISS
from exception.custom_exception import DocumentPortalException
from utils.model_loader import ModelLoader




class DocumentIngestor:
    SUPPORTED_EXTENSIONS = {'.pdf','.docx','.txt','.md'}
    def __init__(self, temp_dir:str ="data/multi_doc_chat", faiss_dir:str = "faiss_index", session_id :str | None = None):
        try:
            self.log = CustomLogger().get_logger()
            self.temp_dir = temp_dir
            self.faiss_dir = faiss_dir
            self.session_id = session_id

            self.session_id = session_id or f"Session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            self.session_temp_dir = self.temp_dir/ self.session_id
            self.session_faiss_dir = self.faiss_dir /self.session_id
            self.session_temp_dir.mkdir(parents = True, exist_ok = True)
            self.session_faiss_dir.mkdir(parents = True , exist_ok=True)


            self.model_loader = ModelLoader()
            self.log.info(
                "DocumentIngestor initialized"
                temp_base=str(self.temp_dir),
                faiss_base=str(self.faiss_dir),
                session_id=self.session_id
                temp_path=str(self.session_temp_dir),
                faiss_path=str(self.session_faiss_dir)
            )




        except Exception as e:
            self.log.error(f"Failed to create directories: {str(e)}")
            raise Exception(f"Failed to create directories: {str(e)}")


    def ingest_files(self):
        try:

            documents =[]
            for uploaded_file in self.uploaded_files:
                    ext = Path(uploaded_file.name).suffix.lower()
                    if ext not in self.SUPPORTED_EXTENSIONS:
                        self.log.warning("Unsupported file type:", filename= uploaded_file.name)
                        continue

                    unique_filename = f"{uuid.uuid4().hex[:8]}{ext}"
                    temp_path = self.session_temp_dir / unique_filename

                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.read())
                    self.log.info("File saved to:", session_id = self.session_id, filename = uploaded_file.name, saved_as=str(temp_path))

                    if ext == ".pdf":
                        loader = PyPDFLoader(str(temp_path))
                    elif ext == ".docx":
                        loader = Docx2txtLoader(str(temp_path))
                    elif ext == ".txt":
                        loader = TextLoader(str(temp_path))
                    elif ext == ".md":
                        loader = TextLoader(str(temp_path))
                    else:
                        self.log.warning("Unsupported file type:", filename= uploaded_file.name)
                        continue
                    
                    docs = loader.load()
                    documents.extend(docs)

                    if not documents:
                        self.log.warning("No documents loaded")
                        raise DocumentPortalException("No documents loaded")


                    self.log.info("Documents loaded successfully", session_id = self.session_id, num_docs = len(documents))
                    return documents

                    
                    
            

        except Exception as e:
            self.log.error(f"Failed to ingest files: {str(e)}")
            raise DocumentPortalException(f"Failed to ingest files: {str(e)}")

    def _create_retriever(self, documents: List[str]):
        try:
            

        except Exception as e:
            self.log.error(f"Failed to create retriever: {str(e)}")
            raise DocumentPortalException(f"Failed to create retriever: {str(e)}")
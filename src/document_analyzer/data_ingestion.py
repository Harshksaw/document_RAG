import os
import sys
from datetime import datetime
import fitz  # PyMuPDF
from utils.model_loader import ModelLoader
from logger import GLOBAL_LOGGER as log
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from model.models import *
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from prompt.prompt_library import PROMPT_REGISTRY # type: ignore

class DocumentAnalyzer:
    """
    Analyzes documents using a pre-trained model.
    Automatically logs all actions and supports session-based organization.
    """
    def __init__(self):
        try:
            
            self.log = CustomLogger()
            self.data_dir  = data_dir or os.getenv("DATA_STORAGE_PATH", os.path.join(os.getcwd(), "data", "document_analysis"))
            self.session_id = session_id or  f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            self.session_path = os.path.join(self.data_dir, self.session_id)
            os.makedirs(self.session_path , exist_ok=True)
        
        except Exception as e:
            log.error("Failed to initialize DocumentAnalyzer", error=str(e))
            raise DocumentPortalException("Initialization error", sys) from e


    def save_pdf(self):
        pass
    
    def read_pdf(self):
        pass
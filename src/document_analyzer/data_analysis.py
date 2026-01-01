import os
from utils.model_loader import ModelLoader
from models.model import Metadata
from exception.custom_exception import DocumentPortalException
from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import JsonOutputParser
from logger.custom_logger import CustomLogger
from prompt.prompt_library import *

class DocumentAnalyzer:
    
    def __init__(self):
        self.log = CustomLogger().get_logger(__name__)
        
        try:
            self.loader = ModelLoader()
            self.llm = self.loader.load_llm()
            
            #prepare parser
            self.parser = JsonOutputParser(pydanctic_obeject=Metadata)
            self.fixing_parser - OutputFixingParser.from_llm(self.llm, self.parser)
            
            self.prompt = PROMPT_REGISTRY["document_analysis"]
            
            self.log.info("DocumentAnalyzer initialized successfully")
            
            
            
        except Exception as e:
            self.log.error(f"Error initializing DocumentAnalyzer: {e}")
            raise DocumentPortalException("Error initializing DocumentAnalyzer", e) from e
        
    
    def analyze_metadata(self):
        pass
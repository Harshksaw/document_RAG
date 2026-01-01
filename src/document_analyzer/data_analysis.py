
import sys
from utils.model_loader import ModelLoader
from models.model import *
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
            self.parser = JsonOutputParser(pydantic_object=Metadata)
            self.fixing_parser = OutputFixingParser.from_llm(self.llm, self.parser)
            
            self.prompt = PROMPT_REGISTRY["document_analysis"]
            
            self.log.info("DocumentAnalyzer initialized successfully")
            
            
            
        except Exception as e:
            self.log.error(f"Error initializing DocumentAnalyzer: {e}")
            raise DocumentPortalException("Error initializing DocumentAnalyzer", sys) from e
        
    
    def analyze_document(self, document_text:str)->dict:
        
        try:
            chain= self.prompt | self.llm | self.fixing_parser
            
            self.log.info("Metadata  analysis chain intialized")
            
            
            response = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                "document_text": document_text
            })
            
            self.log.info("Document analyzed successfully", keys=list(response.keys()   ))
            return response 
            
        except Exception as e:
            self.log.error(f"Error analyzing document: {e}")
            raise DocumentPortalException("Error analyzing document", sys) from e
            raise DocumentPortalException("Error analyzing document", e) from e
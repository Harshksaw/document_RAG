
import sys
from utils.model_loader import ModelLoader
from model.models import *
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
        
    
    def analyze_document(self, document_text:str, max_chars:int=15000)->dict:
        """
        Analyze document metadata.
        For large documents, only uses first few pages for metadata extraction.
        
        Args:
            document_text: Full document text
            max_chars: Maximum characters to analyze (default 15000 ≈ first 5-10 pages)
        """
        try:
            # For metadata extraction, use only the beginning of the document
            # (title, author, date, etc. are usually in first few pages)
            text_sample = document_text[:max_chars]
            
            if len(document_text) > max_chars:
                self.log.info(
                    "Large document detected, analyzing first portion only",
                    total_chars=len(document_text),
                    sample_chars=len(text_sample)
                )
            
            chain= self.prompt | self.llm | self.fixing_parser
            
            self.log.info("Metadata analysis chain initialized")
            
            response = chain.invoke({
                "format_instructions": self.parser.get_format_instructions(),
                "document_text": text_sample
            })
            
            self.log.info("Document analyzed successfully", keys=list(response.keys()))
            return response 
            
        except Exception as e:
            self.log.error(f"Error analyzing document: {e}")
            raise DocumentPortalException("Error analyzing document", sys) from e
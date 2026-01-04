import sys
from pathlib import Path    
import fitz

from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException 
from prompt.prompt_library import PROMPT_REGISTRY
from utils.model_loader import ModelLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field

class ComparisonResult(BaseModel):
    page_number: str = Field(description="Page number")
    status: str = Field(description="Change status (e.g., 'CHANGED', 'NO CHANGE')")
    comparison: str = Field(description="Comparison details")

class SummaryResponse(BaseModel):
    results: list[ComparisonResult] = Field(description="List of comparison results per page")

class DocumentComparator:
    def __init__(self):
        load_dotenv()
        self.log = CustomLogger()
        self.loader = ModelLoader()
        self.llm = self.loader.load_model()
        self.parser = JsonOutputParser(pydantic_object=SummaryResponse)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.llm)
        self.prompt = PROMPT_REGISTRY["document_comparison"]
        self.chain =self.prompt | self.llm | self.parser| self.fixing_parser
        self.log.info("DocumentComparator initialized successfully")    





    def compare_documents(self, combined_docs):
        try:
            
            inputs = {
                "combined_docs": combined_docs,
                "format_instruction": self.parser.get_format_instructions()
            }  



            self.log.info("Inputs created successfully")
            response = self.chain.invoke(inputs)
            self.log.info("Response generated successfully")
            return self._format_response(response)
            
            
        except Exception as e:
            self.log.error(f"Error in compare_documents method of DocumentComparator class: {e}")
            raise DocumentPortalException(e, sys) from e
    
    def _format_response(self, response_parsed: dict) -> pd.DataFrame:
        try:
            df = pd.DataFrame(response_parsed['results'])
            self.log.info("Response formatted successfully")    
            return df




        except Exception as e:
            self.log.error(f"Error in _format_response method of DocumentComparator class: {e}")
            raise DocumentPortalException(e, sys) from e
    
    def read_pdf(self):
        pass
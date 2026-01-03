import sys
from pathlib import Path    
import fitz

from logger.custom_logger import CustomLogger
from exceptions.custom_exception import CustomException 
from prompt.prompt_library import PROMPT_REGISTRY
from utils.model_loader import ModelLoader
from langchain_core.outpi

class DocumentComparator:
    def __init__(self):
        load_dotenv()
        self.log = CustomLogger()
        self.loader = ModelLoader()
        self.llm = self.loader.load_model()
        self.parser = JsonOutputParser(pydantic_object=SummaryResponse)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.llm)
        self.prompt = PROMPT_REGISTRY[PromptType.DOCUMENT_COMPARISON]
        self.chain =self.prompt | self.llm | self.parser| self.fixing_parser
        self.log.info("DocumentComparator initialized successfully")    





    def compare_documents(self):
        try:
            pass
            
        except Exception as e:
            self.logger.error("Error in compare_documents method of DocumentComparator class", e)
            raise CustomException(e, sys) from e
    
    def format_reponse(self):
        pass
    
    def read_pdf(self):
        pass
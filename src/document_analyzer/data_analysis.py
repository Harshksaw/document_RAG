import os
import sys
from typing import Dict, Any
from utils.model_loader import ModelLoader
from utils.token_counter import create_token_callback, get_token_counter
from logger import GLOBAL_LOGGER as log
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
            self.loader=ModelLoader()
            
            # Fallback Logic (Consistency with Chat Module)
            default_provider = os.getenv("LLM_PROVIDER", "groq")
            backup_provider = "google" if default_provider == "groq" else "groq"
            
            log.info("Loading DocumentAnalyzer LLM", provider=default_provider)
            primary_llm = self.loader.load_llm(provider=default_provider)
            
            backup_llm = None
            try:
                log.info("Loading Backup LLM for Analyzer", provider=backup_provider)
                backup_llm = self.loader.load_llm(provider=backup_provider)
            except Exception as e:
                log.warning("Failed to load Backup LLM for Analyzer", error=str(e))
                
            if backup_llm:
                self.llm = primary_llm.with_fallbacks([backup_llm])
            else:
                self.llm = primary_llm
            
            # Prepare parsers
            self.parser = JsonOutputParser(pydantic_object=Metadata)
            self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.llm)
            
            self.prompt = PROMPT_REGISTRY["document_analysis"]
            
            log.info("DocumentAnalyzer initialized successfully")
            
            
        except Exception as e:
            log.error(f"Error initializing DocumentAnalyzer: {e}")
            raise DocumentPortalException("Error in DocumentAnalyzer initialization", sys)
        
        
    
    def analyze_document(self, document_text: str) -> Dict[str, Any]:
        """
        Analyze a document's text and extract structured metadata & summary.

        Returns:
            Dict containing 'metadata' and 'token_usage' for the operation.
        """
        try:
            chain = self.prompt | self.llm | self.fixing_parser

            log.info("Meta-data analysis chain initialized")

            # Create token counter callback for this invocation
            token_callback = create_token_callback(operation_type="analyze")

            # Get usage before invocation
            counter = get_token_counter()
            usage_before = counter.get_usage_by_type("analyze")

            response = chain.invoke(
                {
                    "format_instructions": self.parser.get_format_instructions(),
                    "document_text": document_text
                },
                config={"callbacks": [token_callback]}
            )

            # Calculate tokens used in this call
            usage_after = counter.get_usage_by_type("analyze")
            tokens_used = {
                "input_tokens": usage_after["input_tokens"] - usage_before["input_tokens"],
                "output_tokens": usage_after["output_tokens"] - usage_before["output_tokens"],
                "total_tokens": usage_after["total_tokens"] - usage_before["total_tokens"]
            }

            log.info(
                "Metadata extraction successful",
                keys=list(response.keys()),
                token_usage=tokens_used
            )

            return {"metadata": response, "token_usage": tokens_used}

        except Exception as e:
            log.error("Metadata analysis failed", error=str(e))
            raise DocumentPortalException("Metadata extraction failed", sys)
        
    
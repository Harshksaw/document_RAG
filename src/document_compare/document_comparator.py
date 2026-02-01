import sys
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
import pandas as pd
from langchain_core.output_parsers import JsonOutputParser
from langchain.output_parsers import OutputFixingParser
from utils.model_loader import ModelLoader
from utils.token_counter import create_token_callback, get_token_counter
from logger import GLOBAL_LOGGER as log
from exception.custom_exception import DocumentPortalException
from prompt.prompt_library import PROMPT_REGISTRY
from model.models import SummaryResponse, PromptType

class DocumentComparatorLLM:
    def __init__(self):
        load_dotenv()
        self.loader = ModelLoader()
        self.llm = self.loader.load_llm()
        self.parser = JsonOutputParser(pydantic_object=SummaryResponse)
        self.fixing_parser = OutputFixingParser.from_llm(parser=self.parser, llm=self.llm)
        self.prompt = PROMPT_REGISTRY[PromptType.DOCUMENT_COMPARISON.value]
        self.chain = self.prompt | self.llm | self.parser
        log.info("DocumentComparatorLLM initialized", model=self.llm)

    def compare_documents(self, combined_docs: str) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Compare documents and return results with token usage.

        Returns:
            Tuple of (DataFrame with comparison results, token_usage dict)
        """
        try:
            inputs = {
                "combined_docs": combined_docs,
                "format_instruction": self.parser.get_format_instructions()
            }

            # Create token counter callback for this invocation
            token_callback = create_token_callback(operation_type="compare")

            # Get usage before invocation
            counter = get_token_counter()
            usage_before = counter.get_usage_by_type("compare")

            log.info("Invoking document comparison LLM chain")
            response = self.chain.invoke(inputs, config={"callbacks": [token_callback]})

            # Calculate tokens used in this call
            usage_after = counter.get_usage_by_type("compare")
            tokens_used = {
                "input_tokens": usage_after["input_tokens"] - usage_before["input_tokens"],
                "output_tokens": usage_after["output_tokens"] - usage_before["output_tokens"],
                "total_tokens": usage_after["total_tokens"] - usage_before["total_tokens"]
            }

            log.info(
                "Chain invoked successfully",
                response_preview=str(response)[:200],
                token_usage=tokens_used
            )
            return self._format_response(response), tokens_used
        except Exception as e:
            log.error("Error in compare_documents", error=str(e))
            raise DocumentPortalException("Error comparing documents", sys)

    def _format_response(self, response_parsed: list[dict]) -> pd.DataFrame: #type: ignore
        try:
            df = pd.DataFrame(response_parsed)
            return df
        except Exception as e:
            log.error("Error formatting response into DataFrame", error=str(e))
            DocumentPortalException("Error formatting response", sys)
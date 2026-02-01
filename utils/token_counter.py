"""
Token counter utility for tracking LLM token usage across different operation types.
Provides both a callback handler for LangChain and a centralized counter.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from collections import defaultdict
from threading import Lock
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from logger import GLOBAL_LOGGER as log


@dataclass
class TokenUsage:
    """Token usage for a single LLM call."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


@dataclass
class OperationTokenUsage:
    """Token usage aggregated by operation type."""
    operation_type: str
    call_count: int = 0
    usage: TokenUsage = field(default_factory=TokenUsage)

    def add_usage(self, usage: TokenUsage):
        self.call_count += 1
        self.usage = self.usage + usage


class TokenCounter:
    """
    Centralized token counter that tracks usage by operation type.
    Thread-safe singleton implementation.

    Operation types:
        - chat: Conversational RAG queries (includes rewriting + answering)
        - analyze: Document analysis/metadata extraction
        - compare: Document comparison
    """

    _instance: Optional["TokenCounter"] = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._usage_by_type: Dict[str, OperationTokenUsage] = defaultdict(
            lambda: OperationTokenUsage(operation_type="unknown")
        )
        self._session_usage: Dict[str, Dict[str, OperationTokenUsage]] = defaultdict(
            lambda: defaultdict(lambda: OperationTokenUsage(operation_type="unknown"))
        )
        self._lock = Lock()
        self._initialized = True
        log.info("TokenCounter initialized")

    def record_usage(
        self,
        operation_type: str,
        input_tokens: int,
        output_tokens: int,
        session_id: Optional[str] = None
    ):
        """
        Record token usage for an operation.

        Args:
            operation_type: Type of operation (chat, analyze, compare)
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            session_id: Optional session ID for session-level tracking
        """
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens
        )

        with self._lock:
            # Initialize if needed
            if operation_type not in self._usage_by_type:
                self._usage_by_type[operation_type] = OperationTokenUsage(
                    operation_type=operation_type
                )
            self._usage_by_type[operation_type].add_usage(usage)

            # Session-level tracking
            if session_id:
                if operation_type not in self._session_usage[session_id]:
                    self._session_usage[session_id][operation_type] = OperationTokenUsage(
                        operation_type=operation_type
                    )
                self._session_usage[session_id][operation_type].add_usage(usage)

        log.info(
            "Token usage recorded",
            operation_type=operation_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=usage.total_tokens,
            session_id=session_id
        )

    def get_usage_by_type(self, operation_type: str) -> Dict[str, Any]:
        """Get token usage for a specific operation type."""
        with self._lock:
            if operation_type not in self._usage_by_type:
                return {
                    "operation_type": operation_type,
                    "call_count": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0
                }
            op_usage = self._usage_by_type[operation_type]
            return {
                "operation_type": operation_type,
                "call_count": op_usage.call_count,
                "input_tokens": op_usage.usage.input_tokens,
                "output_tokens": op_usage.usage.output_tokens,
                "total_tokens": op_usage.usage.total_tokens
            }

    def get_all_usage(self) -> Dict[str, Dict[str, Any]]:
        """Get token usage for all operation types."""
        with self._lock:
            return {
                op_type: {
                    "operation_type": op_type,
                    "call_count": op_usage.call_count,
                    "input_tokens": op_usage.usage.input_tokens,
                    "output_tokens": op_usage.usage.output_tokens,
                    "total_tokens": op_usage.usage.total_tokens
                }
                for op_type, op_usage in self._usage_by_type.items()
            }

    def get_session_usage(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """Get token usage for a specific session."""
        with self._lock:
            if session_id not in self._session_usage:
                return {}
            return {
                op_type: {
                    "operation_type": op_type,
                    "call_count": op_usage.call_count,
                    "input_tokens": op_usage.usage.input_tokens,
                    "output_tokens": op_usage.usage.output_tokens,
                    "total_tokens": op_usage.usage.total_tokens
                }
                for op_type, op_usage in self._session_usage[session_id].items()
            }

    def get_total_usage(self) -> Dict[str, int]:
        """Get total token usage across all operations."""
        with self._lock:
            total = TokenUsage()
            total_calls = 0
            for op_usage in self._usage_by_type.values():
                total = total + op_usage.usage
                total_calls += op_usage.call_count
            return {
                "total_calls": total_calls,
                "total_input_tokens": total.input_tokens,
                "total_output_tokens": total.output_tokens,
                "total_tokens": total.total_tokens
            }

    def reset(self):
        """Reset all counters."""
        with self._lock:
            self._usage_by_type.clear()
            self._session_usage.clear()
        log.info("TokenCounter reset")


class TokenCounterCallback(BaseCallbackHandler):
    """
    LangChain callback handler that captures token usage from LLM responses.

    Usage:
        callback = TokenCounterCallback(operation_type="chat", session_id="abc123")
        chain.invoke(input, config={"callbacks": [callback]})
    """

    def __init__(self, operation_type: str, session_id: Optional[str] = None):
        super().__init__()
        self.operation_type = operation_type
        self.session_id = session_id
        self.counter = TokenCounter()
        self._current_input_tokens = 0
        self._current_output_tokens = 0

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM finishes. Extracts token usage from response."""
        try:
            # Try to get token usage from LLM output
            input_tokens = 0
            output_tokens = 0

            # Check llm_output for token usage (common location)
            if response.llm_output:
                token_usage = response.llm_output.get("token_usage", {})
                if token_usage:
                    input_tokens = token_usage.get("prompt_tokens", 0) or token_usage.get("input_tokens", 0)
                    output_tokens = token_usage.get("completion_tokens", 0) or token_usage.get("output_tokens", 0)

                # Groq-specific format
                if "usage" in response.llm_output:
                    usage = response.llm_output["usage"]
                    input_tokens = usage.get("prompt_tokens", input_tokens)
                    output_tokens = usage.get("completion_tokens", output_tokens)

            # Check generations for usage_metadata (Google AI format)
            if response.generations:
                for gen_list in response.generations:
                    for gen in gen_list:
                        if hasattr(gen, "generation_info") and gen.generation_info:
                            usage_meta = gen.generation_info.get("usage_metadata", {})
                            if usage_meta:
                                input_tokens = usage_meta.get("prompt_token_count", input_tokens)
                                output_tokens = usage_meta.get("candidates_token_count", output_tokens)

                        # Check message for usage_metadata
                        if hasattr(gen, "message") and hasattr(gen.message, "usage_metadata"):
                            usage_meta = gen.message.usage_metadata
                            if usage_meta:
                                input_tokens = getattr(usage_meta, "input_tokens", input_tokens)
                                output_tokens = getattr(usage_meta, "output_tokens", output_tokens)

            if input_tokens > 0 or output_tokens > 0:
                self.counter.record_usage(
                    operation_type=self.operation_type,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    session_id=self.session_id
                )
            else:
                log.debug(
                    "No token usage found in LLM response",
                    operation_type=self.operation_type
                )

        except Exception as e:
            log.warning("Failed to extract token usage", error=str(e))


def get_token_counter() -> TokenCounter:
    """Get the singleton TokenCounter instance."""
    return TokenCounter()


def create_token_callback(
    operation_type: str,
    session_id: Optional[str] = None
) -> TokenCounterCallback:
    """
    Create a token counter callback for use with LangChain chains.

    Args:
        operation_type: Type of operation (chat, analyze, compare)
        session_id: Optional session ID for session-level tracking

    Returns:
        TokenCounterCallback instance to pass to chain.invoke()
    """
    return TokenCounterCallback(operation_type=operation_type, session_id=session_id)

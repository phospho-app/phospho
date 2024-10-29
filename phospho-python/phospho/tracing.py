import logging
from typing import List, Dict, Optional, Union

from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor

logger = logging.getLogger(__name__)


class ListSpanProcessor(SpanProcessor):
    """
    A simple span processor that exports all spans to a list.
    """

    def __init__(
        self,
        spans_to_export: List[Span],
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        # OpenTelemetry does not support nested types in attributes
        metadata: Optional[
            Dict[
                str,
                Union[
                    int,
                    bool,
                    str,
                    float,
                    List[int],
                    List[bool],
                    List[str],
                    List[float],
                ],
            ]
        ] = None,
    ):
        self.spans_to_export = spans_to_export
        self.task_id = task_id
        self.session_id = session_id
        self.metadata = metadata

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        # Adds the span to the list of spans to be exported
        if self.task_id:
            span.set_attribute("phospho.task_id", self.task_id)
        if self.session_id:
            span.set_attribute("phospho.session_id", self.session_id)
        if self.metadata:
            # Add "phospho.metadata" attribute to each key
            metadata = {f"phospho.metadata.{k}": v for k, v in self.metadata.items()}
            span.set_attributes(metadata)
        self.spans_to_export.append(span)

    def on_end(self, span: ReadableSpan) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        # pylint: disable=unused-argument
        return True


def init_instrumentations():
    """
    Initialize all instrumentations, based on the installed packages.

    Run `pip install phospho[tracing]` to install all the instrumentations.
    """

    def is_module_installed(module_name: str) -> bool:
        try:
            __import__(module_name)
            return True
        except ImportError:
            return False

    if is_module_installed("openai"):
        try:
            from opentelemetry.instrumentation.openai import OpenAIInstrumentor

            instrumentor = OpenAIInstrumentor(
                enrich_assistant=False,
                enrich_token_usage=False,
            )
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace OpenAI, install opentelemetry-instrumentation-openai"
            )

    if is_module_installed("mistralai"):
        try:
            from opentelemetry.instrumentation.mistralai import MistralAiInstrumentor

            instrumentor = MistralAiInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace MistralAI, install opentelemetry-instrumentation-mistralai"
            )

    if is_module_installed("ollama"):
        try:
            from opentelemetry.instrumentation.ollama import OllamaInstrumentor

            instrumentor = OllamaInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Ollama, install opentelemetry-instrumentation-ollama"
            )

    if is_module_installed("anthropic"):
        try:
            from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

            instrumentor = AnthropicInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Anthropic, install opentelemetry-instrumentation-anthropic"
            )

    if is_module_installed("cohere"):
        try:
            from opentelemetry.instrumentation.cohere import CohereInstrumentor

            instrumentor = CohereInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Cohere, install opentelemetry-instrumentation-cohere"
            )

    if is_module_installed("google-generativeai"):
        try:
            from opentelemetry.instrumentation.google_generativeai import (
                GoogleGenerativeAIInstrumentor,
            )

            instrumentor = GoogleGenerativeAIInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace GoogleGenerativeAI, install opentelemetry-instrumentation-google-generativeai"
            )

    if is_module_installed("pinecone"):
        try:
            from opentelemetry.instrumentation.pinecone import PineconeInstrumentor

            instrumentor = PineconeInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Pinecone, install opentelemetry-instrumentation-pinecone"
            )

    if is_module_installed("qdrant"):
        try:
            from opentelemetry.instrumentation.qdrant import QdrantInstrumentor

            instrumentor = QdrantInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Qdrant, install opentelemetry-instrumentation-qdrant"
            )

    # if is_module_installed("langchain"):
    #     try:
    #         from opentelemetry.instrumentation.langchain import LangchainInstrumentor

    #         instrumentor = LangchainInstrumentor()
    #         instrumentor.instrument()
    #     except ImportError:
    #         logger.warning(
    #             "To trace Langchain, install opentelemetry-instrumentation-langchain"
    #         )

    if is_module_installed("lancedb"):
        try:
            from opentelemetry.instrumentation.lancedb import LancedbInstrumentor

            instrumentor = LancedbInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Lancedb, install opentelemetry-instrumentation-lancedb"
            )

    # if is_module_installed("chromadb"):
    #     try:
    #         from opentelemetry.instrumentation.chromadb import ChromadbInstrumentor

    #         instrumentor = ChromadbInstrumentor()
    #         instrumentor.instrument()
    #     except ImportError:
    #         logger.warning(
    #             "To trace Chromadb, install opentelemetry-instrumentation-chromadb"
    #         )

    if is_module_installed("transformers"):
        try:
            from opentelemetry.instrumentation.transformers import (
                TransformersInstrumentor,
            )

            instrumentor = TransformersInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Transformers, install opentelemetry-instrumentation-transformers"
            )

    if is_module_installed("together"):
        try:
            from opentelemetry.instrumentation.together import TogetherInstrumentor

            instrumentor = TogetherInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Together, install opentelemetry-instrumentation-together"
            )

    if is_module_installed("llamaindex"):
        try:
            from opentelemetry.instrumentation.llamaindex import LlamaIndexInstrumentor

            instrumentor = LlamaIndexInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace LlamaIndex, install opentelemetry-instrumentation-llamaindex"
            )

    if is_module_installed("milvus"):
        try:
            from opentelemetry.instrumentation.milvus import MilvusInstrumentor

            instrumentor = MilvusInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Milvus, install opentelemetry-instrumentation-milvus"
            )

    if is_module_installed("haystack"):
        try:
            from opentelemetry.instrumentation.haystack import HaystackInstrumentor

            instrumentor = HaystackInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Haystack, install opentelemetry-instrumentation-haystack"
            )

    if is_module_installed("bedrock"):
        try:
            from opentelemetry.instrumentation.bedrock import BedrockInstrumentor

            instrumentor = BedrockInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Bedrock, install opentelemetry-instrumentation-bedrock"
            )

    if is_module_installed("sagemaker"):
        try:
            from opentelemetry.instrumentation.sagemaker import SagemakerInstrumentor

            instrumentor = SagemakerInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Sagemaker, install opentelemetry-instrumentation-sagemaker"
            )

    if is_module_installed("replicate"):
        try:
            from opentelemetry.instrumentation.replicate import ReplicateInstrumentor

            instrumentor = ReplicateInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Replicate, install opentelemetry-instrumentation-replicate"
            )

    if is_module_installed("vertexai"):
        try:
            from opentelemetry.instrumentation.vertexai import VertexaiInstrumentor

            instrumentor = VertexaiInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Vertexai, install opentelemetry-instrumentation-vertexai"
            )

    if is_module_installed("watsonx"):
        try:
            from opentelemetry.instrumentation.watsonx import WatsonxInstrumentor

            instrumentor = WatsonxInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Watsonx, install opentelemetry-instrumentation-watsonx"
            )

    if is_module_installed("weaviate"):
        try:
            from opentelemetry.instrumentation.weaviate import WeaviateInstrumentor

            instrumentor = WeaviateInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Weaviate, install opentelemetry-instrumentation-weaviate"
            )

    if is_module_installed("alephalpha"):
        try:
            from opentelemetry.instrumentation.alephalpha import AlephalphaInstrumentor

            instrumentor = AlephalphaInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Alephalpha, install opentelemetry-instrumentation-alephalpha"
            )

    if is_module_installed("marqo"):
        try:
            from opentelemetry.instrumentation.marqo import MarqoInstrumentor

            instrumentor = MarqoInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning(
                "To trace Marqo, install opentelemetry-instrumentation-marqo"
            )

    if is_module_installed("groq"):
        try:
            from opentelemetry.instrumentation.groq import GroqInstrumentor

            instrumentor = GroqInstrumentor()
            instrumentor.instrument()
        except ImportError:
            logger.warning("To trace Groq, install opentelemetry-instrumentation-groq")

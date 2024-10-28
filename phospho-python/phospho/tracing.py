import inspect
from typing import Any, Dict, List, Optional

from opentelemetry.context import (
    _SUPPRESS_INSTRUMENTATION_KEY,
    Context,
)
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor
from phospho.client import Client


class ListSpanProcessor(SpanProcessor):
    """
    A simple span processor that exports all spans to a list.
    """

    def __init__(
        self,
        spans_to_export: List[Span],
        task_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
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
            span.set_attribute("phospho.metadata", self.metadata)
        self.spans_to_export.append(span)

    def on_end(self, span: ReadableSpan) -> None:
        # Do nothing
        pass

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        # pylint: disable=unused-argument
        return True


def init_instrumentations():
    instrumentor = OpenAIInstrumentor(
        enrich_assistant=False,
        enrich_token_usage=False,
    )
    instrumentor.instrument()

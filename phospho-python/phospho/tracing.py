from typing import List, Dict, Optional, Union

from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor


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
    # TODO : Add the other instrumentations, based on the installed packages
    from opentelemetry.instrumentation.openai import OpenAIInstrumentor

    instrumentor = OpenAIInstrumentor(
        enrich_assistant=False,
        enrich_token_usage=False,
    )
    instrumentor.instrument()

from typing import Dict, Any, List, Union, Optional
from phospho.utils import convert_to_jsonable_dict

try:
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import LLMResult
    from langchain_core.callbacks import BaseCallbackHandler, AsyncCallbackHandler
    from langchain_core.agents import AgentAction, AgentFinish
except ImportError:
    pass


class PhosphoLangchainCallbackHandler(BaseCallbackHandler):
    """Phospho callback handler for Langchain."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        tick: float = 0.5,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.session_id = session_id

        import phospho

        self.phospho = phospho
        self.phospho.init(api_key=api_key, project_id=project_id, tick=tick)

        # Content to be logged
        self.main_input = None
        self.main_output = None
        self.intermediate_inputs = []
        self.intermediate_outputs = []

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""
        print("START llm")

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        **kwargs: Any,
    ) -> Any:
        """Run when Chat Model starts running."""

    def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        """Run on new LLM token. Only available when streaming is enabled."""

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Run when LLM ends running."""

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when LLM errors."""

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Any:
        """Run when chain starts running."""
        inputs_to_log = convert_to_jsonable_dict(inputs)

        parent_run_id = kwargs.get("parent_run_id", False)
        if parent_run_id is None:
            # Start of the main chain
            self.main_input = inputs_to_log
        else:
            self.intermediate_inputs.append(inputs_to_log)

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""

        if isinstance(outputs, str):
            output_to_log = outputs
        else:
            output_to_log = convert_to_jsonable_dict(outputs)

        parent_run_id = kwargs.get("parent_run_id", False)
        if parent_run_id is None:
            # End of the main chain
            self.main_output = output_to_log

            self.phospho.log(
                input=self.main_input,
                output=output_to_log,
                session_id=self.session_id,
                raw_input={"intermediate_inputs": self.intermediate_inputs},
                raw_output={"intermediate_outputs": self.intermediate_outputs},
                **kwargs,
            )
        else:
            self.intermediate_outputs.append(output_to_log)

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when chain errors."""

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Run when tool ends running."""

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when tool errors."""

    def on_text(self, text: str, **kwargs: Any) -> Any:
        """Run on arbitrary text."""

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run on agent action."""

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> Any:
        """Run on agent end."""


class PhosphoLangchaiAsyncCallbackHandler(AsyncCallbackHandler):
    """Phospho async callback handler for Langchain."""

    def __init__(self, **kwargs: Any) -> None:
        # TODO
        raise NotImplementedError()

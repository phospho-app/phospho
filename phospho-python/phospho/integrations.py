from typing import Dict, Any, Union, Optional

try:
    from langchain_core.callbacks import BaseCallbackHandler, AsyncCallbackHandler

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

        def on_chain_start(
            self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
        ) -> Any:
            """Run when chain starts running."""

            inputs_to_log = inputs

            parent_run_id = kwargs.get("parent_run_id", False)
            if parent_run_id is None:
                # Start of the main chain
                self.main_input = inputs_to_log
            else:
                self.intermediate_inputs.append(inputs_to_log)

        def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
            """Run when chain ends running."""

            output_to_log = outputs

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
            # Log the error
            output_to_log = str(error)
            self.phospho.log(
                input=self.main_input,
                output=output_to_log,
                session_id=self.session_id,
                raw_input={"intermediate_inputs": self.intermediate_inputs},
                raw_output={"intermediate_outputs": self.intermediate_outputs},
                **kwargs,
            )

        def on_tool_start(
            self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
        ) -> Any:
            """Run when tool starts running."""
            # Add to intermediate inputs
            self.intermediate_inputs.append(input_str)

        def on_tool_end(self, output: str, **kwargs: Any) -> Any:
            """Run when tool ends running."""
            # Add to intermediate outputs
            self.intermediate_outputs.append(output)

        def on_tool_error(
            self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
        ) -> Any:
            """Run when tool errors."""
            # Add to intermediate outputs as error
            self.intermediate_outputs.append(str(error))

    class PhosphoLangchaiAsyncCallbackHandler(AsyncCallbackHandler):
        """Phospho async callback handler for Langchain."""

        def __init__(self, **kwargs: Any) -> None:
            # TODO
            raise NotImplementedError()

except ImportError:
    pass

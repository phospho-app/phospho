from typing import Callable, Dict, Any, Optional

try:
    from langchain_core.callbacks import BaseCallbackHandler, AsyncCallbackHandler

    class PhosphoLangchainCallbackHandler(BaseCallbackHandler):
        """Phospho callback handler for Langchain."""

        def __init__(
            self,
            api_key: Optional[str] = None,
            project_id: Optional[str] = None,
            session_id: Optional[str] = None,
            input_key: Optional[str] = None,
            output_key: Optional[str] = None,
            tick: float = 0.5,
            version_id: Optional[str] = None,
            base_url: Optional[str] = None,
            **kwargs: Any,
        ) -> None:
            """
            Initialize the Phospho callback handler. This will log the input and output of the main chain.

            The main chain is the one with no `parent_run_id`

            Args:
                api_key (str): Phospho API key.
                project_id (str): Phospho project ID.
                session_id (str): Session ID. This is used to group messages together.
                input_key (str): The inputs of the main chain is a dict.
                    If input_key is not None, the inputs[input_key] will be logged.
                    Otherwise, the dict is directly logged.
                output_key (str): The outputs of the main chain is a dict.
                    If output_key is not None, the outputs[output_key] will be logged.
                    Otherwise, the dict is directly logged.
                tick (float): Logs are sent to phospho every tick seconds. Default is 0.5.
                version_id (str): Version of the app. Used for AB testing.
                base_url (str): Phospho base URL.

            Any other keyword arguments are passed to the Langchain BaseCallbackHandler.
            """
            super().__init__(**kwargs)
            self.session_id = session_id

            import phospho  # Local reference to avoid circular import

            self.phospho = phospho
            self.phospho.init(
                api_key=api_key,
                project_id=project_id,
                tick=tick,
                version_id=version_id,
                base_url=base_url,
                auto_log=False,  # Disable auto logging
            )

            # Content to be logged
            self.main_input = None
            self.main_output = None

            # Input and output keys
            self.input_key = input_key
            self.output_key = output_key

        def on_chain_start(
            self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
        ) -> Any:
            """Run when chain starts running."""

            if self.input_key:
                inputs_to_log = inputs[self.input_key]
            else:
                inputs_to_log = inputs

            parent_run_id = kwargs.get("parent_run_id", False)
            if parent_run_id is None:
                # Start of the main chain
                self.main_input = inputs_to_log

        def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
            """
            Run when chain ends running.

            This calls the phospho logging function. The main input and output are logged.

            Extra keyword arguments are passed to the phospho log function.
            """

            if self.output_key:
                output_to_log = outputs[self.output_key]
            else:
                output_to_log = outputs

            parent_run_id = kwargs.get("parent_run_id", False)
            if parent_run_id is None and self.main_input is not None:
                # End of the main chain
                self.main_output = output_to_log
                self.phospho.log(
                    input=self.main_input,
                    output=output_to_log,
                    session_id=self.session_id,
                    **kwargs,
                )

    class PhosphoLangchaiAsyncCallbackHandler(AsyncCallbackHandler):
        """Phospho async callback handler for Langchain."""

        def __init__(self, **kwargs: Any) -> None:
            # TODO
            raise NotImplementedError()

except ImportError:
    pass


def wrap_openai(wrap: Callable) -> None:
    """
    Wrap OpenAI API calls with a logging function.
    """
    try:
        from openai.resources.chat import completions

        global original_create
        original_create = completions.Completions.create
        completions.Completions.create = wrap(original_create, auto_log=True)
    except ImportError:
        pass

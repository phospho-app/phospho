import inspect
import logging
import time
from random import sample
from typing import Any, Callable, Dict, Iterator, List, Literal, Optional

from phospho.utils import generate_version_id
from pydantic import BaseModel, Field
from rich import print

from phospho import lab
from phospho.client import Client

logger = logging.getLogger(__name__)


def adapt_dict_to_agent_function(
    dict_to_adapt: dict, agent_function: Callable[[Any], Any]
) -> Optional[dict]:
    """This function adapts a dict to match the signature of the agent_function.

    - If all the dict's keys can be mapped to the agent_function's parameters, this returns the dict.
    - If the dict has more keys than the agent_function's parameters, this returns a new dict that
        only contains the keys that are in the agent_function's parameters.

    If nothing can be done, this returns None.
    """

    # The compatibility is based on the parameters names in the agent function signature
    agent_function_signature: inspect.Signature = inspect.signature(agent_function)
    dict_keys = set(dict_to_adapt.keys())
    agent_function_inputs = set(agent_function_signature.parameters.keys())

    if dict_keys == agent_function_inputs:
        # The dict is compatible with the agent function
        return dict_to_adapt
    elif dict_keys <= agent_function_inputs:
        # The agent function takes more inputs than the dict provides
        # Check if those are optional in the agent function
        for key in agent_function_inputs - dict_keys:
            if (
                agent_function_signature.parameters[key].default
                is inspect.Parameter.empty
            ):
                # The agent function takes a non optional input that the dict does not provide
                # We can't adapt the dict to the agent function
                # Log what key is missing from the agent_function
                logger.warning(
                    f"Dict {dict_to_adapt} is not compatible with agent function {agent_function.__name__}: {key} is missing from the dict"
                )
                return None
        # All of the additional inputs are optional in the agent function
        # So the dict is compatible with the agent function
        return dict_to_adapt
    elif dict_keys >= agent_function_inputs:
        # We filter the dict to only keep the keys that are in the agent function signature
        new_dict = {
            key: dict_to_adapt[key] for key in agent_function_inputs if key in dict_keys
        }

        # Log info that we filtered dict keys
        logger.info(
            f"Reduced the number of keys of dict {dict_to_adapt} to match the agent function {agent_function.__name__}: removed {dict_keys - agent_function_inputs}"
        )
        return new_dict
    else:
        # Check if the agent_function has an argument for any number of keyword arguments
        for param in agent_function_signature.parameters.values():
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                return dict_to_adapt

    return None


def adapt_to_sample_size(list_to_sample, sample_size):
    """
    Adapt list_to_sample to match the sample_size, either by upsampling or downsampling.
    """
    if sample_size < 0:
        raise ValueError("sample_size must be positive")
    if (len(list_to_sample) == 0) or (sample_size == 0):
        return []

    if sample_size is None:
        # None = all the tasks
        sampled_list = list_to_sample
    elif sample_size == 0:
        # 0 = no tasks
        sampled_list = []
    elif len(list_to_sample) > sample_size:
        # Downsample
        sampled_list = sample(list_to_sample, sample_size)
    elif len(list_to_sample) < sample_size:
        # Upsample
        # Duplicate the tasks
        duplicated_tasks = list_to_sample * int(1 + sample_size / len(list_to_sample))
        # Sample the remaining tasks
        sampled_list = list_to_sample + sample(
            duplicated_tasks,
            sample_size % len(duplicated_tasks) - len(list_to_sample),
        )
    else:
        sampled_list = list_to_sample
    return sampled_list


class Loader:
    """
    Abstract class for Loaders
    """

    def __iter__(self):
        raise NotImplementedError

    def __next__(self) -> lab.Message:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError


class BacktestLoader(Loader):
    sampled_tasks: Iterator
    sample_size: int

    def __init__(
        self,
        client: Client,
        agent_function: Callable[[Any], Any],
        sample_size: Optional[int] = 10,
    ):
        # Pull the logs from phospho
        # TODO : Add filters
        tasks = client.fetch_tasks()
        if len(tasks) == 0:
            print(f"[red]No data found in project {client.project_id}[/red]")
            self.sampled_tasks = iter([])
            return

        # Filter the tasks to only keep the ones that are compatible with the agent function
        messages: List[lab.Message] = []
        for task in tasks:
            # Convert to a lab.Message
            message = lab.Message(
                role="user",
                content=task.input,
                metadata={
                    "task_id": task.id,
                    "test_id": task.test_id,
                },
            )
            messages.append(message)

        self.sampled_tasks = iter(
            adapt_to_sample_size(list_to_sample=messages, sample_size=sample_size)
        )
        if sample_size is None:
            sample_size = len(messages)
        self.sample_size = sample_size

    def __iter__(self):
        return self

    def __next__(self) -> lab.Message:
        """
        Return the next message to evaluate
        """
        return next(self.sampled_tasks)

    def __len__(self) -> int:
        return self.sample_size


class DatasetLoader(Loader):
    def __init__(
        self,
        agent_function: Callable[[Any], Any],
        path: str,
    ):
        """
        Loads a dataset from a file and returns an iterator over the dataset.

        The dataset can be a .csv, .json or .xlsx file.

        The columns of the dataset must match the signature of the agent function to evaluate. Extra columns will be ignored.

        Moreover, if metrics is "compare", the dataset must have a column "output" that will be used as the old output.

        Example:

            ```
            phospho_test = phospho.PhosphoTest()

            @phospho_test.test(
                source_loader="dataset",
                source_loader_params={
                    "path": "golden_dataset.xlsx",
                },
                metrics=["evaluate"],
            )
            def test_santa_dataset(input: str):
                santa_claus_agent = SantaClausAgent()
                return santa_claus_agent.answer(messages=[{"role": "user", "content": input}])
            ```

        In this example, the dataset must have a column "input" that will be used as the input of the agent function.
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "You need to install pandas to use the dataset loader. Run `pip install pandas`."
            )

        if path.endswith(".csv"):
            self.df = pd.read_csv(path)
        elif path.endswith(".json"):
            self.df = pd.read_json(path)
        elif path.endswith(".xlsx"):
            self.df = pd.read_excel(path)
        else:
            # TODO : Add more file formats
            raise NotImplementedError(
                f"File format {path.split('.')[-1]} is not supported. Supported formats: .csv, .json, .xlsx"
            )

        # Create an iterator over the dataset
        self.dataset = iter(self.df.to_dict(orient="records"))
        self.function_to_evaluate = agent_function

    def __iter__(self):
        return self

    def __next__(self) -> lab.Message:
        next_item = next(self.dataset)
        id = next_item.pop("id", None)
        role = next_item.pop("role", "user").lower()
        content = next_item.pop("content", "")
        created_at = next_item.pop("created_at", None)
        message = lab.Message(
            id=id,
            role=role,
            content=content,
            created_at=created_at,
            metadata=next_item,
        )
        return message

    def __len__(self):
        return self.df.shape[0]


class FunctionToEvaluate(BaseModel):
    function: Callable[[Any], Any]
    function_name: str
    source_loader: Optional[Literal["backtest", "dataset"]] = None
    source_loader_params: Dict[str, Any] = Field(default_factory=dict)


class PhosphoTest:
    client: Client
    functions_to_evaluate: Dict[str, FunctionToEvaluate]
    version_id: str
    phospho: Any

    def __init__(
        self,
        version_id: Optional[str] = None,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        This is used to backtest an agent with phospho.

        Sample code:

        ```
        phospho_test = phospho.PhosphoTest()

        @phospho_test.test
        def test_santa(**inputs):
            santa_claus_agent = SantaClausAgent()
            return santa_claus_agent.answer(**inputs)

        phospho_test.run()
        ```
        """
        import phospho

        self.client = Client(api_key=api_key, project_id=project_id, base_url=base_url)
        self.functions_to_evaluate = {}
        if version_id is None:
            version_id = generate_version_id()
        self.version_id = version_id
        self.phospho = phospho
        self.phospho.init(
            api_key=api_key,
            project_id=project_id,
            base_url=base_url,
            version_id=version_id,
        )

    def test(
        self,
        fn: Optional[Callable[[Any], Any]] = None,
        source_loader: Optional[Literal["backtest", "dataset"]] = None,
        source_loader_params: Optional[Dict[str, Any]] = None,
    ) -> Callable[[Any], Any]:
        """
        Add this as a decorator on top of the evaluation function.
        """

        if source_loader_params is None:
            source_loader_params = {}

        def meta_wrapper(
            fn: Callable[[Any], Any],
            source_loader: Optional[Literal["backtest", "dataset"]],
            source_loader_params: Dict[str, Any],
        ):
            self.functions_to_evaluate[fn.__name__] = FunctionToEvaluate(
                function=fn,
                function_name=fn.__name__,
                source_loader=source_loader,
                source_loader_params=source_loader_params,
            )
            return fn

        if fn is None:
            return lambda fn: meta_wrapper(fn, source_loader, source_loader_params)
        else:
            return meta_wrapper(fn, source_loader, source_loader_params)

    def log(
        self,
        input: str,
        output: str,
        **kwargs,
    ):
        """
        Log the input and output to phospho
        """
        self.phospho.log(
            input=input, output=output, version_id=self.version_id, **kwargs
        )

    def flush(self):
        self.phospho.flush()

    def run(
        self,
        executor_type: Literal["parallel", "sequential", "parallel_jobs"] = "parallel",
        max_parallelism: int = 20,
    ):
        """
        Run the tests
        """

        # Start timer
        start_time = time.time()
        print(f"Running tests for version_id: '{self.version_id}'")
        print(f"Executor type: {executor_type}")
        print(f"Max parallelism: {max_parallelism}")

        # os.environ["PHOSPHO_VERSION_ID"] = self.version_id

        # Collect the functions.
        for function_name, function_to_eval in self.functions_to_evaluate.items():
            print(f"Running test: [green]🧪 {function_name}[/green]")
            # Load the tasks
            if function_to_eval.source_loader is None:
                # Just execute the function
                try:
                    function_to_eval.function()
                except Exception as e:
                    print(f"[red]Error running {function_name}:[/red] {e}")
                # Go to the next function
                continue

            messages: Loader
            if function_to_eval.source_loader == "backtest":
                messages = BacktestLoader(
                    client=self.client,
                    agent_function=function_to_eval.function,
                    **function_to_eval.source_loader_params,
                )
            elif function_to_eval.source_loader == "dataset":
                messages = DatasetLoader(
                    agent_function=function_to_eval.function,
                    **function_to_eval.source_loader_params,
                )
            else:
                raise NotImplementedError(
                    f"Source loader {function_to_eval.source_loader} is not implemented"
                )

            async def evaluate(message: lab.Message):
                try:
                    # The function is fed with a message and all the metadata
                    function_input = {
                        "message": message,
                        **message.metadata,
                    }
                    # Extra metadata is removed so that the function can be called
                    adapted_function_input = adapt_dict_to_agent_function(
                        function_input, function_to_eval.function
                    )
                    response = function_to_eval.function(**adapted_function_input)
                    # Log the input and output to phospho
                    self.log(
                        input=message.content,
                        output=response,
                    )
                except Exception as e:
                    print(f"[red]Error running {function_name}:[/red] {e}")
                    return None

                return lab.JobResult(
                    value=response,
                    result_type=lab.ResultType.dict,
                )

            workload = lab.Workload(
                jobs=[
                    lab.Job(
                        id=function_name,
                        job_function=evaluate,
                    )
                ]
            )
            workload.run(
                messages=messages,
                executor_type=executor_type,
                max_parallelism=max_parallelism,
            )

        self.flush()
        # Stop timer
        end_time = time.time()

        # Display a summary of the results
        print("🧪[green]Finished running the tests![/green]")
        print(f"Total time: {end_time - start_time:.3f} seconds")
        print(
            f"[b][green]Results:[/green] https://platform.phospho.ai/org/ab-testing?b={self.version_id}[/b]"
        )

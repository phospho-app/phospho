import os
import concurrent.futures
import logging
import inspect
import time

from types import GeneratorType
from typing import List, Dict, Optional, Callable, Any, Literal
from pydantic import BaseModel

from phospho.client import Client
from phospho.tasks import Task
from phospho import extractor

from random import sample
from pprint import pprint

logger = logging.getLogger(__name__)


class TestInput(BaseModel, extra="allow"):
    function_input: dict  # What we pass to the function
    input: Optional[str] = None
    additional_input: Optional[dict] = None
    output: Optional[str] = None
    task_id: Optional[str] = None

    @classmethod
    def from_task(cls, task: Task) -> "TestInput":
        # Combine the input and additional_input
        if task.content.additional_input is not None:
            function_input = task.content.additional_input
        elif task.content.input is not None:
            function_input.update({"input": task.content.input})
        else:
            function_input = {}

        return TestInput(function_input=function_input, **task.content_as_dict())


def adapt_dict_to_agent_function(
    dict_to_adapt: dict, agent_function: Callable[[Any], Any]
) -> Optional[dict]:
    """This function adapts a dict to match the signature of an agent function.

    If the dict is compatible with the agent function, this returns the dict.

    If the dict is not compatible with the agent function, this returns a new dict that
    is compatible with the agent function, but that has less keys.

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


def adapt_task_to_agent_function(
    task: Task, agent_function: Callable[[Any], Any]
) -> Optional[TestInput]:
    """This function adapts a task to match the signature of an agent function.

    If the task is compatible with the agent function, this returns the task.

    If the task is not compatible with the agent function, this returns a new task that
    is compatible with the agent function, but that has less inputs.

    If nothing can be done, this returns None.
    """

    # The compatibility is based on the parameters names in the agent function signature
    agent_function_signature: inspect.Signature = inspect.signature(agent_function)
    task_inputs = set(task.content.additional_input.keys())
    agent_function_inputs = set(agent_function_signature.parameters.keys())

    if task_inputs == agent_function_inputs:
        # The task is compatible with the agent function
        return TestInput.from_task(task)
    elif task_inputs <= agent_function_inputs:
        # The agent function takes more inputs than the task provides
        # Check if those are optional in the agent function
        for key in agent_function_inputs - task_inputs:
            if (
                agent_function_signature.parameters[key].default
                is inspect.Parameter.empty
            ):
                # The agent function takes a non optional input that the task does not provide
                # We can't adapt the task to the agent function
                # Log what key is missing from the agent_function
                logger.warning(
                    f"Task {task.id} is not compatible with agent function {agent_function.__name__}: {key} is missing from the task"
                )
                return None
        # All of the additional inputs are optional in the agent function
        # So the task is compatible with the agent function
        return TestInput.from_task(task)
    elif task_inputs >= agent_function_inputs:
        # We filter the task to only keep the keys that are in the agent function signature
        new_task = TestInput(
            function_input={
                key: task.content.additional_input[key] for key in agent_function_inputs
            },
            task_id=task.id,
            **task.content_as_dict(),
        )

        # Log info that we filtered task inputs
        logger.info(
            f"Reduced the number of inputs of task {task.id} to match the agent function {agent_function.__name__}: removed {task_inputs - agent_function_inputs}"
        )
        return new_task
    else:
        # Check if the agent_function has an argument for any number of keyword arguments
        for param in agent_function_signature.parameters.values():
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                # The agent function takes a **kwargs argument
                # The task is compatible with the agent function
                return TestInput.from_task(task)

    return None


def adapt_to_sample_size(list_to_sample, sample_size):
    """
    This function will adapt the list to sample to match the sample size.
    """
    if sample_size < 0:
        raise ValueError("sample_size must be positive")

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


class BacktestLoader:
    def __init__(
        self,
        client: Client,
        agent_function: Callable[[Any], Any],
        sample_size: Optional[int] = 10,
    ):
        # Pull the logs from phospho
        # TODO : Add time range filter
        # TODO : Add pull from dataset
        tasks = client.tasks.get_all()
        if len(tasks) == 0:
            raise ValueError("No tasks found in the project")

        # Filter the tasks to only keep the ones that are compatible with the agent function
        tasks_linked_to_function = []
        for task in tasks:
            adapted_task = adapt_task_to_agent_function(task, agent_function)
            if adapted_task is not None:
                tasks_linked_to_function.append(
                    {"test_input": adapted_task, "agent_function": agent_function}
                )

        self.sampled_tasks = iter(
            adapt_to_sample_size(
                list_to_sample=tasks_linked_to_function, sample_size=sample_size
            )
        )

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.sampled_tasks)

    def __len__(self):
        return len(self.sampled_tasks)


class DatasetLoader:
    def __init__(
        self,
        agent_function: Callable[[Any], Any],
        path: str,
        test_n_times: Optional[int] = None,
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

        # If test_n_times is not None, we'll repeat the dataset n times
        if test_n_times is not None:
            self.df = pd.concat([self.df] * test_n_times)

        # Create an iterator over the dataset
        self.dataset = iter(self.df.to_dict(orient="records"))

        self.function_to_evaluate = agent_function

    def __iter__(self):
        return self

    def __next__(self):
        next_item = next(self.dataset)
        # TODO : Verify it has the right columns for the function_to_evaluate
        function_input = adapt_dict_to_agent_function(
            next_item, self.function_to_evaluate
        )
        test_input = TestInput(
            function_input=function_input,
            input=next_item.get("input", None),
            output=next_item.get("output", None),
        )
        return {
            "test_input": test_input,
            "agent_function": self.function_to_evaluate,
        }

    def __len__(self):
        return self.df.shape[0]


class PhosphoTest:
    client: Client
    functions_to_evaluate: Dict[str, Any]
    test_id: Optional[str]

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
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
        self.client = Client(api_key=api_key, project_id=project_id)
        self.functions_to_evaluate: Dict[str, Any] = {}
        self.test_id: Optional[str] = None

    def test(
        self,
        fn: Optional[Callable[[Any], Any]] = None,
        source_loader: Literal["backtest", "dataset"] = "backtest",
        source_loader_params: Optional[Dict[str, Any]] = None,
        metrics: Optional[List[Literal["compare", "evaluate"]]] = None,
    ) -> Callable[[Any], Any]:
        """
        Add this as a decorator on top of the evaluation function.
        """

        # TODO: Add task_name as a parameter
        # TODO: Add custom instructions for comparison and evaluation as a parameter
        if metrics is None:
            metrics = ["evaluate"]

        if source_loader_params is None:
            source_loader_params = {}

        def meta_wrapper(
            fn: Optional[Callable[[Any], Any]] = None,
            source_loader: Literal["backtest", "dataset"] = "backtest",
            source_loader_params: Optional[Dict[str, Any]] = None,
            metrics: Optional[List[Literal["compare", "evaluate"]]] = None,
        ):
            self.functions_to_evaluate[fn.__name__] = {
                "function": fn,
                "function_name": fn.__name__,
                "source_loader": source_loader,
                "source_loader_params": source_loader_params,
                "metrics": metrics,
            }

            return fn

        if fn is None:
            return lambda fn: meta_wrapper(
                fn, source_loader, source_loader_params, metrics
            )
        else:
            return meta_wrapper(fn, source_loader, source_loader_params, metrics)

    def get_output_from_agent(
        self,
        function_input: Dict[str, Any],
        agent_function: Callable[[Any], Any],
        metric_name: str,
    ):
        """
        This function will return the output of the agent given an input
        """
        print(
            f"Calling {agent_function.__name__} with input {function_input.__repr__()}"
        )

        # TODO : Make it so that that we use input or additional_input depending on the
        # signature (input type) of the agent function

        os.environ["PHOSPHO_TEST_METRIC"] = metric_name
        new_output = agent_function(**function_input)

        # Handle generators
        if isinstance(new_output, GeneratorType):
            full_resp = ""
            for response in new_output:
                full_resp += response or ""
            new_output_str = extractor.detect_str_from_output(full_resp)
        else:
            new_output_str = extractor.detect_str_from_output(new_output)

        print(f"Output {agent_function.__name__}: {new_output_str}")

        return new_output_str

    def evaluate(self, task_to_evaluate: Dict[str, Any]):
        """
        Run the evaluation pipeline on the task
        """
        test_input: TestInput = task_to_evaluate["test_input"]
        agent_function = task_to_evaluate["agent_function"]

        # Get the output from the agent
        context_input = test_input.input
        new_output_str = self.get_output_from_agent(
            function_input=test_input.function_input,
            agent_function=agent_function,
            metric_name="evaluate",
        )

        # Ask phospho: what's the best answer to the context_input ?
        print("Evaluating with phospho")

    def compare(
        self, task_to_compare: Dict[str, Any]
    ) -> None:  # task: Task, agent_function: Callable[[Any], Any]):
        """
        Compares the output of the task with the output of the agent function
        """

        test_input: TestInput = task_to_compare["test_input"]
        agent_function = task_to_compare["agent_function"]
        print("Comparing task id: ", test_input)

        # Get the output from the agent
        context_input = test_input.input
        old_output_str = test_input.output
        new_output_str = self.get_output_from_agent(
            function_input=test_input.function_input,
            agent_function=agent_function,
            metric_name="compare",
        )

        # Ask phospho: what's the best answer to the context_input ?
        print(f"Comparing with phospho (task: {test_input.id})")
        self.client.compare(
            context_input=context_input,
            old_output=old_output_str,
            new_output=new_output_str,
            test_id=self.test_id,
        )

    def run(
        self,
        executor_type: Literal["parallel", "sequential"] = "parallel",
    ):
        """
        Backtesting: This function pull all the tasks logged to phospho and run the agent on them.
        """

        # Start timer
        start_time = time.time()

        self.test = self.client.create_test(
            summary={
                function_name: {
                    "source_loader": function_to_eval["source_loader"],
                    "source_loader_params": function_to_eval["source_loader_params"],
                    "metrics": function_to_eval["metrics"],
                }
                for function_name, function_to_eval in self.functions_to_evaluate.items()
            }
        )
        self.test_id = self.test.id
        print(f"Starting test: {self.test_id}")
        os.environ["PHOSPHO_TEST_ID"] = self.test_id

        for function_name, function_to_eval in self.functions_to_evaluate.items():
            print(f"Running tests for: {function_name}")
            source_loader = function_to_eval["source_loader"]
            source_loader_params = function_to_eval["source_loader_params"]
            metrics = function_to_eval["metrics"]
            agent_function = function_to_eval["function"]

            if source_loader == "backtest":
                tasks_linked_to_function = BacktestLoader(
                    client=self.client,
                    agent_function=agent_function,
                    **source_loader_params,
                )
            elif source_loader == "dataset":
                tasks_linked_to_function = DatasetLoader(
                    agent_function=agent_function,
                    **source_loader_params,
                )
            else:
                raise NotImplementedError(
                    f"Source loader {source_loader} is not implemented"
                )

            for metric in metrics:
                if metric == "evaluate":
                    import phospho

                    # For evaluate, we'll need to init phospho and use .log
                    phospho.init(self.client.api_key, self.client.project_id)
                    evaluation_function = self.evaluate
                elif metric == "compare":
                    evaluation_function = self.compare
                else:
                    # TODO : Add more metrics
                    raise NotImplementedError(
                        f"Metric {metric} is not implemented. Implemented metrics: 'compare', 'evaluate'"
                    )

                # Evaluate the tasks in parallel
                # TODO : Add more executor types to handle different types of parallelism
                if executor_type == "parallel":
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        # Submit tasks to the executor
                        # executor.map(self.evaluate_a_task, task_to_evaluate)
                        executor.map(evaluation_function, tasks_linked_to_function)
                elif executor_type == "sequential":
                    for task_function in tasks_linked_to_function:
                        evaluation_function(task_function)
                elif executor_type == "async":
                    # TODO : Do more tests with async executor and async agent_function
                    import asyncio

                    loop = asyncio.get_event_loop()
                    loop.run_until_complete(
                        asyncio.gather(
                            *[
                                evaluation_function(task_function)
                                for task_function in tasks_linked_to_function
                            ]
                        )
                    )
                else:
                    raise NotImplementedError(
                        f"Executor type {self.executor_type} is not implemented"
                    )

                if metric == "evaluate":
                    phospho.consumer.send_batch()

        # Stop timer
        end_time = time.time()

        # Display a summary of the results
        print("Finished running the tests")
        print(f"Total number of tasks: {len(list(tasks_linked_to_function))}")
        print(f"Total time: {end_time - start_time} seconds")
        print(f"Test id: {self.test_id}")
        print("Waiting for evaluation to finish...")
        # Mark the test as completed and get results
        test_result = self.client.update_test(test_id=self.test_id, status="completed")
        print("Test result:")
        pprint(test_result.model_dump())

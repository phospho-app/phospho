import asyncio
import concurrent.futures
import logging
from typing import Awaitable, Callable, Dict, Iterable, List, Literal, Optional, Union

import nest_asyncio

import phospho.lab.job_library as job_library

from .models import JobConfig, JobResult, Message, ResultType

logger = logging.getLogger(__name__)


try:
    # This is a workaround to avoid the error "RuntimeError: This event loop is already running" in jupyter notebooks
    # Related issue: https://github.com/NVIDIA/NeMo-Guardrails/issues/112
    nest_asyncio.apply()
except Exception as e:
    logger.info(
        "Could not apply nest_asyncio. This is not a problem if you are not running in a jupyter notebook."
        + f"Error: {e}"
    )


class Job:
    id: str
    job_function: Union[
        Callable[..., JobResult],
        Callable[..., Awaitable[JobResult]],  # For async jobs
    ]
    # Stores the current config and the possible config values as an instanciated pydantic object
    config: JobConfig
    # message.id -> job_result
    results: Dict[str, JobResult]

    # List of alternative results for the job
    alternative_results: List[Dict[str, JobResult]]
    # Stores all the possible config from the model
    alternative_configs: List[JobConfig]

    def __init__(
        self,
        id: Optional[str] = None,
        job_function: Optional[
            Union[
                Callable[..., JobResult],
                Callable[..., Awaitable[JobResult]],  # For async jobs
            ]
        ] = None,
        name: Optional[str] = None,
        config: Optional[JobConfig] = None,
    ):
        """
        A job is a function that takes a message and a set of parameters and returns a result.
        It stores the result.
        """

        if job_function is None and name is None:
            raise ValueError("Please provide a job_function or a job_name.")

        if name is not None:
            # from the module .job_library import the function with the name job_name
            job_function = getattr(job_library, name)
        assert job_function is not None, "Please provide a job_function or a job_name."
        self.job_function = job_function

        if id is None:
            if name is not None:
                id = name
            else:
                # Make it the name of the function
                id = job_function.__name__

        self.id = id

        # message.id -> job_result
        self.results: Dict[str, JobResult] = {}

        # If the config values are provided, store them
        if config is not None:
            self.config = config
            # generate all the possible configuration from the model
            self.alternative_configs = self.config.generate_configurations()
        else:
            logger.warning("No job_config provided. Running with empty config")
            self.config = JobConfig()
            self.alternative_configs = []

        self.alternative_results = []

    def run(self, message: Message) -> JobResult:
        """
        Run the job on the message.
        """
        # TODO: Infer for each message its context (if any)
        # The context is the previous messages of the session

        params = self.config.model_dump()

        if asyncio.iscoroutinefunction(self.job_function):
            result = asyncio.run(self.job_function(message, **params))
        else:
            result = self.job_function(message, **params)

        if result is None:
            logger.error(f"Job {self.id} returned None for message {message.id}.")
            result = JobResult(
                job_id=self.id,
                result_type=ResultType.error,
                value=None,
            )

        self.results[message.id] = result
        return result

    def _run_on_alternative_configurations(
        self, message: Message
    ) -> List[List[JobResult]]:
        """
        Run the job on the message with all the possible configurations except the default.
        Results are appended to the job_predictions attribute.
        """
        if len(self.alternative_results) == 0:
            raise ValueError(
                "No alternative configurations to run the job on. Please run .optimize first."
            )

        for alternative_config_index in range(0, len(self.alternative_configs)):
            params = self.alternative_configs[alternative_config_index].model_dump()
            if asyncio.iscoroutinefunction(self.job_function):
                prediction = asyncio.run(self.job_function(message, **params))
            else:
                prediction = self.job_function(message, **params)

            if prediction is None:
                logger.error(
                    f"Job {self.id} returned None for message {message.id} on alternative config run."
                )
                prediction = JobResult(
                    job_id=self.id,
                    result_type=ResultType.error,
                    value=None,
                )

            # Add the prediction to the job_predictions
            current_predictions = self.alternative_results[alternative_config_index]
            current_predictions[message.id] = prediction
            self.alternative_results[alternative_config_index] = current_predictions

        return self.alternative_results

    def optimize(self, accuracy_threshold: float = 1.0, min_count: int = 10) -> None:
        """
        After having run the job on all the alternative configurations,
        optimize the job by comparing all the predictions to the results with the default configuration.
        - If the current configuration is the optimal, do nothing.
        - If the current configuration is not the optimal, update the config attribute.

        For now, we just check if the accuracy is above the threshold.
        """
        # Check that we have enough predictions to start the optimization
        if len(self.results) < min_count:
            return

        accuracies: List[float] = []
        # For each alternative config, we compute the accuracy_vector
        for alternative_config_index in range(0, len(self.alternative_configs)):
            # Results are considered the groundtruth. Compare the alternative results to this ref
            accuracy_vector = [
                1
                if self.alternative_results[alternative_config_index][key]
                == self.results[key]
                else 0
                for key in self.results
            ]

            accuracy = sum(accuracy_vector) / len(accuracy_vector)
            accuracies.append(accuracy)

        # The latest items are the most preferred ones
        # The instanciated config is the reference one (most truthful)
        # We want to take the latest one that is above the threshold.
        for i in range(len(accuracies) - 1, -1, -1):
            if accuracies[i] > accuracy_threshold:
                logger.info(
                    f"Found a less costly config with accuracy of {accuracies[i]}. Swapping to it."
                )
                # This configuration becames the default configuration
                self.config = self.alternative_configs[i]
                # We keep the results of the more costly config as the results
                # Might be an empty list
                self.alternative_configs = self.alternative_configs[i + 1 :]
                # We drop the results of the other sub-optimal configurations
                # Might be an empty list
                self.alternative_results = self.alternative_results[i + 1 :]
                break

    def __repr__(self):
        # Make every parameter on a new line
        concatenated_params = "\n".join(
            [f"    {k}: {v}" for k, v in self.params.items()]
        )
        return f"Job(\n  job_id={self.id},\n  job_name={self.job_function.__name__},\n  params={{\n{concatenated_params}\n  }}\n)"


class Workload:
    jobs: List[Job]
    # Result is a mapping of message.id -> job_id -> JobResult
    results: Dict[str, Dict[str, JobResult]]

    def __init__(self):
        """
        A Workload is a set of jobs to be performed on a message.
        """
        self.jobs = []
        self.results = {}

    def add_job(self, job: Job):
        """
        Add a job to the workload.
        """
        self.jobs.append(job)

    @classmethod
    def from_config(cls, config: dict) -> "Workload":
        """
        Create a Workload from a configuration dictionary.
        """

        workload = cls()
        # Create the jobs from the configuration
        # TODO : Adds some kind of validation
        for job_id, job_config in config["jobs"].items():
            job_config_model = JobConfig(**job_config.get("config", {}))
            job = Job(
                id=job_id,
                name=job_config["name"],
                config=job_config_model,
            )
            workload.add_job(job)

        return workload

    @classmethod
    def from_file(cls, config_filename: str = "phospho-config.yaml") -> "Workload":
        """
        Create a Workload from a configuration file.
        """
        if config_filename.endswith(".yaml") or config_filename.endswith(".yml"):
            import yaml

            with open(config_filename) as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
        else:
            raise NotImplementedError(
                f"File extension {config_filename.split('.')[-1]} is not supported. Use .from_config() instead."
            )
        return cls.from_config(config)

    def run(
        self,
        messages: Iterable[Message],
        executor_type: Literal["parallel", "sequential"] = "parallel",
    ) -> Dict[str, Dict[str, JobResult]]:
        """
        Runs all the jobs on the message.

        Returns: a mapping of message.id -> job_id -> job_result
        """

        # Run the jobs sequentially on every message
        # TODO : Run the jobs in parallel on every message
        for job in self.jobs:
            if executor_type == "parallel":
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Submit tasks to the executor
                    # executor.map(self.evaluate_a_task, task_to_evaluate)
                    executor.map(job.run, messages)
            elif executor_type == "sequential":
                for one_message in messages:
                    job.run(one_message)
            else:
                raise NotImplementedError(
                    f"Executor type {executor_type} is not implemented"
                )

        # Collect the results:
        # Result is a mapping of message.id -> job_id -> job_result
        results: Dict[str, Dict[str, JobResult]] = {}
        for one_message in messages:
            results[one_message.id] = {}
            for job in self.jobs:
                results[one_message.id][job.id] = job.results[one_message.id]

        self.results = results
        return results

    def __repr__(self):
        concatenated_jobs = "\n".join([f"  {job}" for job in self.jobs])
        return f"Workload(jobs=[\n{concatenated_jobs}\n])"

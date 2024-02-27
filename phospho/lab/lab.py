import asyncio
import concurrent.futures
import logging
from typing import Callable, Dict, Iterable, List, Literal, Optional, Union

import nest_asyncio

import phospho.lab.job_library as job_library

from .models import Any, EmptyConfig, JobConfig, JobResult, Message, ResultType
from .utils import generate_configurations

# This is a workaround to avoid the error "RuntimeError: This event loop is already running" in jupyter notebooks
nest_asyncio.apply()
logger = logging.getLogger(__name__)


class Job:
    job_id: str
    params: Dict[str, Any]
    job_results: Dict[str, JobResult]
    job_predictions: List[
        List[JobResult]
    ]  # First indice is the config index in job_configurations
    job_config: JobConfig  # Stores the current config and the possible config values as an instanciated pydantic object
    job_configurations: List[JobConfig]  # Stores all the possible config from the model
    job_function: Union[
        Callable[..., JobResult],
        Callable[..., asyncio.Future[JobResult]],  # For async jobs
    ]

    def __init__(
        self,
        job_function: Optional[Callable[..., JobResult]] = None,
        job_name: Optional[str] = None,
        job_id: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        job_config: JobConfig = None,
    ):
        """
        A job is a function that takes a message and a set of parameters and returns a result.
        It stores the result.
        """

        if params is None:
            params = {}
        self.params = params

        if job_function is None and job_name is None:
            raise ValueError("Please provide a job_function or a job_name.")

        if job_name is not None:
            # from the module .job_library import the function with the name job_name
            job_function = getattr(job_library, job_name)
        assert job_function is not None, "Please provide a job_function or a job_name."
        self.job_function = job_function

        if job_id is None:
            if job_name is not None:
                job_id = job_name
            else:
                # Make it the name of the function
                job_id = job_function.__name__

        self.job_id = job_id

        # message.id -> job_result
        self.job_results: Dict[str, JobResult] = {}

        # If the config values are provided, store them
        if job_config is not None:
            self.job_config = job_config
            # generate all the possible configuration from the model
            self.job_configurations = generate_configurations(self.job_config)
        else:
            logger.warning("No job_config provided. Running with empty config")
            self.job_config = EmptyConfig()
            self.job_configurations = generate_configurations(self.job_config)

    def run(self, message: Message) -> JobResult:
        """
        Run the job on the message.
        """
        # TODO: Infer for each message its context (if any)
        # The context is the previous messages of the session

        if asyncio.iscoroutinefunction(self.job_function):
            result = asyncio.run(
                self.job_function(
                    message,
                    **self.params,
                    job_config=self.job_config,
                )
            )
        else:
            result = self.job_function(
                message,
                **self.params,
                job_config=self.job_config,
            )

        if result is None:
            logger.error(f"Job {self.job_id} returned None for message {message.id}.")
            result = JobResult(
                job_id=self.job_id,
                result_type=ResultType.error,
                value=None,
            )

        self.job_results[message.id] = result
        return result

    def run_on_alternative_configurations(self, message: Message) -> List[JobResult]:
        """
        Run the job on the message with all the possible configurations except the default.
        Results are appended to the job_predictions attribute.
        """
        for alternative_config_index in range(0, len(self.job_configurations)):
            if asyncio.iscoroutinefunction(self.job_function):
                prediction = asyncio.run(
                    self.job_function(
                        message,
                        **self.params,
                        job_config=self.job_configurations[alternative_config_index],
                    )
                )
            else:
                prediction = self.job_function(
                    message,
                    **self.params,
                    job_config=self.job_configurations[alternative_config_index],
                )

            if prediction is None:
                logger.error(
                    f"Job {self.job_id} returned None for message {message.id} on alternative config run."
                )
                prediction = JobResult(
                    job_id=self.job_id,
                    result_type=ResultType.error,
                    value=None,
                )

            # Add the prediction to the job_predictions
            current_predictions = self.job_predictions[alternative_config_index]
            current_predictions.append(prediction)
            self.job_predictions[alternative_config_index] = current_predictions

    def optimize(self, accuracy_threshold=1.0, min_count=10):
        """
        Optimize the job by comparing all the predictions to the results with the default configuration.
        If the current configuration is the optimal, do nothing.
        If the current configuration is not the optimal, update the job_config attribute.
        For now, we just check if the accuracy is above the threshold.
        """
        # Check that we have enough predictions to start the optimization
        if len(self.job_results) < min_count:
            return

        accuracies = []
        # For each alternative config, we compute the accuracy_vector
        for alternative_config_index in range(0, len(self.job_configurations)):
            # Generate the accuracy vector
            accuracy_vector = [
                1 if output == label else 0
                for output, label in zip(
                    self.job_predictions[alternative_config_index], self.job_results
                )
            ]
            # Compute the accuracy
            accuracy = sum(accuracy_vector) / len(accuracy_vector)
            # Add it to the accuracies
            accuracies.append(accuracy)

        # We want to take the last item of the accuracy list with a good enough accuracy (defined as above the threshold)
        for i in range(len(accuracies) - 1, -1, -1):
            if accuracies[i] > accuracy_threshold:
                logger.info(
                    f"Found a less costly config with accuracy of {accuracies[i]}. Swapping to it."
                )
                # This configuration becames the default configuration
                self.job_config = self.job_configurations[i]
                # We keep the results of the more costly config as the results
                self.job_configurations = self.job_configurations[
                    i + 1 :
                ]  # Might be an empty list
                # We drop the results of the other sub-optimal configurations
                self.job_predictions = self.job_predictions[
                    i + 1 :
                ]  # Might be an empty list

    def __repr__(self):
        # Make every parameter on a new line
        concatenated_params = "\n".join(
            [f"    {k}: {v}" for k, v in self.params.items()]
        )

        return f"Job(\n  job_id={self.job_id},\n  job_name={self.job_function.__name__},\n  params={{\n{concatenated_params}\n  }}\n )"


class Workload:
    jobs: List[Job]
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
            job = Job(
                job_id=job_id,
                job_name=job_config["name"],
                params=job_config.get("params", {}),
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
                results[one_message.id][job.job_id] = job.job_results[one_message.id]

        self.results = results
        return results

    def __repr__(self):
        concatenated_jobs = "\n".join([f"  {job}" for job in self.jobs])
        return f"Workload(jobs=[\n{concatenated_jobs}\n])"

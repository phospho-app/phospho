import asyncio
import concurrent.futures
import logging
from typing import (
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Union,
    Any,
)


import phospho.lab.job_library as job_library

from .models import JobConfig, JobResult, Message, ResultType

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        for c in self.alternative_configs:
            self.alternative_results.append({})

    async def async_run(self, message: Message) -> JobResult:
        """
        Asynchronously run the job on the message.
        """
        logger.debug(f"Running job {self.id} on message {message.id}.")
        params = self.config.model_dump()

        if asyncio.iscoroutinefunction(self.job_function):
            result = await self.job_function(message, **params)
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

    async def async_run_on_alternative_configurations(
        self, message: Message
    ) -> List[Dict[str, JobResult]]:
        """
        Asynchronously run the job on the message in all the laternative configurations, except the default.
        Results are appended to the job_predictions attribute.
        """
        if len(self.alternative_configs) == 0:
            logger.warning("No alternative configuarations found. Skipping.")
            return [{}]

        for alternative_config_index in range(0, len(self.alternative_configs)):
            params = self.alternative_configs[alternative_config_index].model_dump()
            if asyncio.iscoroutinefunction(self.job_function):
                prediction = await self.job_function(message, **params)
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

            # Add the prediction to the alternative_results
            self.alternative_results[alternative_config_index][message.id] = prediction

        return self.alternative_results

    def optimize(self, accuracy_threshold: float = 1.0, min_count: int = 10) -> None:
        """
        After having run the job on all the alternative configurations,
        optimize the job by comparing all the predictions to the results with the default configuration.
        - If the current configuration is the optimal, do nothing.
        - If the current configuration is not the optimal, update the config attribute.

        For now, we just check if the accuracy is above the threshold.
        """
        # Check that the alternative_results are not empty
        if len(self.alternative_results) == 0:
            logger.warning(
                """
                No alternative results found. 
                This can be caused by not having alternative configs or if you didn't called the 
                async_run_on_alternative_configurations on the jobs. 
                Skipping.
                """
            )
            return

        # Check that each alternative_result is each the same length as the results
        for alternative_result in self.alternative_results:
            if len(alternative_result) != len(self.results):
                logger.error(
                    """
                    The alternative_results are not the same length as the results. 
                    Skipping.
                    """
                )
                return

        # Check that we have enough predictions to start the optimization
        if len(self.results) < min_count:
            logger.info("Not enough results to start the optimization. Skipping.")
            return

        accuracies: List[float] = []
        # For each alternative config, we compute the accuracy_vector
        for alternative_config_index in range(0, len(self.alternative_configs)):
            # Results are considered the groundtruth. Compare the alternative results to this ref
            accuracy_vector = [
                1
                if self.alternative_results[alternative_config_index][key].value
                == self.results[key].value
                else 0
                for key in self.results
            ]

            accuracy = sum(accuracy_vector) / len(accuracy_vector)
            accuracies.append(accuracy)

        # DEBUG
        print(f"accuracies: {accuracies}")

        # The latest items are the most preferred ones
        # The instanciated config is the reference one (most truthful)
        # We want to take the latest one that is above the threshold.
        for i in range(len(accuracies) - 1, -1, -1):
            if accuracies[i] >= accuracy_threshold:
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
        return f"Job(\n  job_id={self.id},\n  job_name={self.job_function.__name__},\n  config={{\n{self.config}\n  }}\n)"


class Workload:
    jobs: List[Job]
    # Result is a mapping of message.id -> job_id -> JobResult
    _results: Optional[Dict[str, Dict[str, JobResult]]]

    def __init__(self):
        """
        A Workload is a set of jobs to be performed on a message.
        """
        self.jobs = []
        self._results = None

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

    async def async_run(
        self,
        messages: Iterable[Message],
        executor_type: Literal["parallel", "sequential"] = "parallel",
        max_parallelism: int = 10,
    ) -> Dict[str, Dict[str, JobResult]]:
        """
        Runs all the jobs on the message.

        Returns: a mapping of message.id -> job_id -> job_result
        """

        # Run the jobs sequentially on every message
        # TODO : Run the jobs in parallel on every message
        for job in self.jobs:
            if executor_type == "parallel":
                # Await all the results
                semaphore = asyncio.Semaphore(max_parallelism)

                async def job_limit_wrap(url):
                    async with semaphore:
                        return await job.async_run(url)

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Submit tasks to the executor
                    executor_results = executor.map(job_limit_wrap, messages)

                await asyncio.gather(*executor_results)
            elif executor_type == "sequential":
                for one_message in messages:
                    await job.async_run(one_message)
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

        self._results = results
        return results

    async def async_run_on_alternative_configurations(
        self,
        messages: Iterable[Message],
        executor_type: Literal["parallel", "sequential"] = "parallel",
    ) -> None:
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
                    executor_predictions = executor.map(
                        job.async_run_on_alternative_configurations, messages
                    )
                # Await all the results
                await asyncio.gather(*executor_predictions)
            elif executor_type == "sequential":
                for one_message in messages:
                    await job.async_run_on_alternative_configurations(one_message)
            else:
                raise NotImplementedError(
                    f"Executor type {executor_type} is not implemented"
                )

        # We do not collect the results here, as we want to keep the alternative results
        # They are stored in the job object, in the alternative_results attribute

    def optimize_jobs(
        self, accuracy_threshold: float = 1.0, min_count: int = 10
    ) -> None:
        """
        After having run the job on all the alternative configurations,
        optimize the job by comparing all the predictions to the results with the default configuration.
        - If the current configuration is the optimal, do nothing.
        - If the current configuration is not the optimal, update the config attribute.

        For now, we just check if the accuracy is above the threshold.
        """
        for job in self.jobs:
            job.optimize(accuracy_threshold=accuracy_threshold, min_count=min_count)

    def __repr__(self):
        concatenated_jobs = "\n".join([f"  {job}" for job in self.jobs])
        return f"Workload(jobs=[\n{concatenated_jobs}\n])"

    @property
    def results(self) -> Optional[Dict[str, Dict[str, JobResult]]]:
        if self._results is None:
            logger.warning("Results are not available. Please run the workload first.")
            return None
        return self._results

    @results.setter
    def results(self, results: Dict[str, Dict[str, JobResult]]):
        self._results = results
        return results

    def results_df(self) -> Any:
        """
        Returns the results as a pandas dataframe
        """
        import pandas as pd

        results = self.results

        if results is None:
            return pd.DataFrame()

        # results is a dict from message.id -> job_id -> job_result
        # Flatten the results such that : every row is a message, and every column is a job_result.value
        # The index is the message.id
        # The columns are the job_id
        # The values are the job_result.value
        results_df = pd.DataFrame.from_dict(
            {
                message_id: {
                    job_id: result.value for job_id, result in job_results.items()
                }
                for message_id, job_results in results.items()
            },
            orient="index",
        )
        return results_df

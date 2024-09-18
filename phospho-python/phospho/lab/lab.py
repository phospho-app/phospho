import asyncio
import concurrent.futures
import itertools
import logging
import random
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Protocol,
    Tuple,
    Union,
)

from tqdm import tqdm

import phospho.client as client
import phospho.lab.job_library as job_library

from .models import (
    EventConfig,
    EventConfigForKeywords,
    EvenConfigForRegex,
    JobConfig,
    JobResult,
    Message,
    ResultType,
    EventDefinition,
    Project,
    Recipe,
)


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

    metadata: Optional[Dict[str, Any]] = None
    workload: Optional["Workload"] = None
    sample: float = 1

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
        metadata: Optional[Dict[str, Any]] = None,
        workload: Optional["Workload"] = None,
        sample: float = 1.0,
    ):
        """
        A job is a function that takes a message and a set of parameters and returns a result.
        It stores the result.

        If the job_function is not provided, it will be fetched from the job_library with the name.

        A job is meant to be run on a Message, inside a Workload. Example:

        ```python
        from phospho import lab

        job = lab.Job(
            id="job_id",
            job_function=lab.job_library.event_detection,
            config=lab.EventConfig(event_name="event_name", event_description="event_description"),
        )

        workload = lab.Workload()
        workload.add_job(job)

        messages = [lab.Message(content="Hello world!")]

        await workload.async_run(messages)
        ```

        Args:
        :param id: The id of the job. If not provided, it will be the name of the job_function. This
        id should be unique to the job.
        :param job_function: The function to run on the message. Can be a sync or async function.
        :param name: If the job_function is not provided, it will be fetched from the job_library using this name.
        This is useful to specify the job_function in config files. If the name is None, it will be equal to the job_id.
        :param config: The configuration of the job. If not provided, the job will run with an empty config.
        :param metadata: Extra metadata to store with the job.
        :param workload: The workload to which the job belongs. This is useful to access the results of other jobs.
        :param sample: The sample rate of the job. If the sample rate is 0.5, the job will run on 50% of the messages.
        :param recipe_id: The id of the recipe that created the job. This is useful to track the origin of the job.
        :param recipe_type: The type of the recipe that created the job.
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
            logger.debug("No job_config provided. Running with empty config")
            self.config = JobConfig()
            self.alternative_configs = []

        self.alternative_results = []
        for c in self.alternative_configs:
            self.alternative_results.append({})

        self.metadata = metadata
        self.workload = workload
        self.sample = sample

    async def async_run(self, message: Message) -> JobResult:
        """
        Asynchronously run the job on a single message.
        """
        logger.debug(f"Running job {self.id} on message {message.id}.")
        params = self.config.model_dump()

        # if 'job' is in the job_function signature, we pass the self object
        # Don't override the job parameter if it's already in the params
        if "job" in self.job_function.__code__.co_varnames and "job" not in params:
            params["job"] = self
        if (
            "workload" in self.job_function.__code__.co_varnames
            and "workload" not in params
        ):
            params["workload"] = self.workload

        if asyncio.iscoroutinefunction(self.job_function):
            result = await self.job_function(message, **params)
        else:
            result = self.job_function(message, **params)

        if result is None:
            logger.error(f"Job {self.id} returned None for message {message.id}.")
            result = JobResult(
                result_type=ResultType.error,
                value=None,
            )

        # Add the job_id to the result
        result.job_id = self.id
        result.job_metadata = self.metadata
        # Store the result
        self.results[message.id] = result

        return result

    async def async_run_on_alternative_configurations(
        self, message: Message
    ) -> List[Dict[str, JobResult]]:
        """
        Asynchronously run the job on the message in all the alternative configurations, except the default.
        Results are appended to the job_predictions attribute.
        """
        if len(self.alternative_configs) == 0:
            logger.warning(
                f"Job {self.id}: No alternative configurations found. Skipping."
            )
            return [{}]

        for alternative_config_index in range(0, len(self.alternative_configs)):
            params = self.alternative_configs[alternative_config_index].model_dump()
            if asyncio.iscoroutinefunction(self.job_function):
                job_result = await self.job_function(message, **params)
            else:
                job_result = self.job_function(message, **params)

            if job_result is None:
                logger.error(
                    f"Job {self.id} returned None for message {message.id} on alternative config run."
                )
                job_result = JobResult(
                    result_type=ResultType.error,
                    value=None,
                )
            # Add the job_id to the result
            job_result.job_id = self.id
            job_result.job_metadata = self.metadata
            # Add the prediction to the alternative_results
            self.alternative_results[alternative_config_index][message.id] = job_result

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
                "Can't run Workload.optimize(): No alternative results found. "
                + "Make sure you called Workload.async_run_on_alternative_configurations() first. "
                + "Skipping."
            )
            return

        # Check that each alternative_result is each the same length as the results
        for alternative_result in self.alternative_results:
            if len(alternative_result) != len(self.results):
                logger.error(
                    "Can't run Workload.optimize(): The alternative_results are not the same length as the results. Skipping."
                )
                return

        # Check that we have enough predictions to start the optimization
        if len(self.results) < min_count:
            logger.info(
                f"Can't run Workload.optimize(): {min_count} results are required, but only {len(self.results)} found. Skipping."
            )
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

        logger.info(f"Accuracies: {accuracies}")

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
        return f"""Job(
    job_id={self.id},
    job_name={self.job_function.__name__},
    config={{\n{self.config}\n  }},
    metadata={self.metadata}
)"""


class MessageCallable(Protocol):
    """
    A function whose first argument is a Message.
    """

    def __call__(self, message: Message, *args: Any, **kwargs: Any) -> Any: ...


class Workload:
    # Jobs is a mapping of job_id -> Job
    jobs: Dict[str, Job]
    # Result is a mapping of message.id -> job_id -> JobResult
    _results: Optional[Dict[str, Dict[str, JobResult]]]

    _valid_project_events: Optional[Dict[str, EventDefinition]] = None

    project_id: Optional[str] = None
    org_id: Optional[str] = None

    def __init__(self, jobs: Optional[List[Union[Job, MessageCallable]]] = None):
        """
        A Workload is a set of jobs to be performed on messages.

        ```python
        from phospho import lab

        workload = lab.Workload()
        workload.add_job(
            job=lab.job_library.event_detection,
            job_config=lab.EventConfig(event_name="event_name", event_description="event_description")
        )

        messages = [lab.Message(content="Hello world!")]

        await workload.async_run(messages)
        ```
        """
        self.jobs = {}
        self._results = None

        if jobs is not None:
            for job in jobs:
                self.add_job(job)

    def add_job(
        self,
        job: Union[Job, MessageCallable],
        job_config: Optional[Union[JobConfig, dict]] = None,
        job_id: Optional[str] = None,
        job_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a job to the workload.

        job: A Job object or a callable function that takes a Message as first argument.
        job_config: The configuration of the job. If not provided, the job will run with an empty config.
        job_id: The id of the job. If not provided, it will be the name of the job_function.
        job_metadata: Extra metadata to store with the job.
        """

        if callable(job):
            job = Job(job_function=job)

        if isinstance(job, Job):
            job.workload = self
        else:
            raise ValueError(
                "Please provide a Job object or a callable function to add_job."
            )

        if job_id is not None:
            job.id = job_id

        if job_config is not None:
            if isinstance(job_config, dict):
                job_config = JobConfig(**job_config)
            job.config = job_config

        if job_metadata is not None:
            job.metadata = job_metadata

        self.jobs[job.id] = job

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
        Create a Workload from a configuration file. Supported file extensions are .yaml and .yml.

        Example of a configuration file to detect user asking for price:
        ```yaml
        jobs:
            detect_user_asking_for_price:  # job id
                name: event_detection      # The name of the job in the job_library
                config:                    # The configuration of the job
                    event_name: user_asking_for_price
                    event_description: User is asking for the price of a product
            detect_user_asking_for_discount:
                name: event_detection
                config:
                    event_name: user_asking_for_discount
                    event_description: User is asking for a discount on a product
        ```
        """
        # TODO: Add support .json
        if config_filename.endswith(".yaml") or config_filename.endswith(".yml"):
            import yaml

            with open(config_filename) as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
        else:
            raise NotImplementedError(
                f"File extension {config_filename.split('.')[-1]} is not supported. Use .from_config() instead."
            )
        return cls.from_config(config)

    @classmethod
    def from_phospho_events(
        cls, event_definitions: List[EventDefinition]
    ) -> "Workload":
        workload = cls()

        for event_definition in event_definitions:
            event_name = event_definition.event_name
            workload.project_id = event_definition.project_id

            logger.debug(
                f"Add event detection job for event {event_definition.event_name}"
            )

            # We stick to the LLM detection engine
            if event_definition.detection_engine == "llm_detection":
                workload.add_job(
                    Job(
                        id=event_name,
                        job_function=job_library.event_detection,
                        config=EventConfig(
                            event_name=event_name,
                            event_description=event_definition.description,
                            event_scope=event_definition.detection_scope,
                            score_range_settings=event_definition.score_range_settings,
                        ),
                        metadata=event_definition.model_dump(),
                    )
                )

            # We use a keyword detection engine
            elif (
                event_definition.detection_engine == "keyword_detection"
                and event_definition.keywords is not None
            ):
                workload.add_job(
                    Job(
                        id=event_name,
                        job_function=job_library.keyword_event_detection,
                        config=EventConfigForKeywords(
                            event_name=event_name,
                            keywords=event_definition.keywords,
                            event_scope=event_definition.detection_scope,
                            score_range_settings=event_definition.score_range_settings,
                        ),
                        metadata=event_definition.model_dump(),
                    )
                )

            # We use a regex pattern to detect the event
            elif (
                event_definition.detection_engine == "regex_detection"
                and event_definition.regex_pattern is not None
            ):
                workload.add_job(
                    Job(
                        id=event_name,
                        job_function=job_library.regex_event_detection,
                        config=EvenConfigForRegex(
                            event_name=event_name,
                            regex_pattern=event_definition.regex_pattern,
                            event_scope=event_definition.detection_scope,
                            score_range_settings=event_definition.score_range_settings,
                        ),
                        metadata=event_definition.model_dump(),
                    )
                )

            else:
                logger.warning(
                    f"Skipping unsupported detection engine {event_definition.detection_engine} for event {event_name}"
                )

        return workload

    @classmethod
    def from_phospho_recipe(
        cls,
        recipe: Recipe,
    ):
        """
        Create a workload for Event detection from a single phospho recipe
        (as defined in the database).
        """
        if recipe.recipe_type != "event_detection":
            raise NotImplementedError(
                f"Recipe type {recipe.recipe_type} is not supported. Only 'event_detection' is supported."
            )

        parameters = {
            **recipe.parameters,
            "recipe_id": recipe.id,
            "recipe_type": recipe.recipe_type,
            "project_id": recipe.project_id,
            "org_id": recipe.org_id,
        }
        logger.debug(f"parameters: {parameters}")
        event = EventDefinition(**parameters)

        if event.recipe_id is None:
            event.recipe_id = recipe.id
        if event.recipe_type is None:
            event.recipe_type = "event_detection"

        return Workload.from_phospho_events([event])

    @classmethod
    def from_phospho_project_config(
        cls,
        project_config: Project,
    ):
        """
        Create a workload from a phospho project configuration.

        To fetch the project configuration, look at `Workload.from_phospho()`
        """
        project_events = project_config.settings.events
        if project_events is None:
            logger.warning(f"Project with id {project_config.id} has no event setup")
            return cls()

        workload = cls.from_phospho_events(list(project_events.values()))
        workload.project_id = project_config.id
        workload.org_id = project_config.org_id
        return workload

    @classmethod
    def from_phospho(
        cls,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Connects to the phospho backend and loads the project configuration as a workload.

        If the `api_key` or the `project_id` are not provided, load the `PHOSPHO_API_KEY` and
        `PHOSPHO_PROJECT_ID` env variables.
        """
        phospho_client = client.Client(
            api_key=api_key, project_id=project_id, base_url=base_url
        )

        # Load the project configuration
        project_config = phospho_client.project_config()
        return cls.from_phospho_project_config(project_config)

    async def async_run(
        self,
        messages: Iterable[Message],
        executor_type: Literal["parallel", "sequential", "parallel_jobs"] = "parallel",
        max_parallelism: int = 10,
    ) -> Dict[str, Dict[str, JobResult]]:
        """
        Runs all the jobs on the message.

        Args:
        :param messages: The messages to run the jobs on.
        :param executor_type: The type of executor to use. Can be "parallel" or "sequential".
        :param max_parallelism: The maximum number of parallel jobs to run per seconds.
            Use this to adhere to rate limits. Only used if executor_type is "parallel" or "parallel_jobs".

        Returns: a mapping of message.id -> job_id -> job_result
        """

        # Run the jobs sequentially on every message
        # TODO : For Jobs, implement a batched_run method that takes a list of messages
        if executor_type == "parallel":
            for job_id, job in self.jobs.items():
                # Await all the results
                semaphore = asyncio.Semaphore(max_parallelism)
                # Create a progress bar
                if hasattr(messages, "__len__"):
                    t = tqdm(total=len(messages))
                else:
                    t = tqdm()

                async def job_limit_wrap(message: Message):
                    # Account for the semaphore (rate limit, max_parallelism)
                    async with semaphore:
                        if job.sample >= 1 or random.random() < job.sample:
                            await job.async_run(message)
                        # Update the progress bar
                        t.update()

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Submit tasks to the executor
                    executor_results = executor.map(job_limit_wrap, messages)

                t.display()
                await asyncio.gather(*executor_results)
                t.close()
        elif executor_type == "parallel_jobs":
            # Create a progress bar
            if isinstance(messages, list):
                t = tqdm(total=len(messages) * len(self.jobs))
            else:
                t = tqdm()

            messages_and_jobs = itertools.product(messages, self.jobs.values())
            semaphore = asyncio.Semaphore(max_parallelism)

            async def message_job_limit_wrap(message_and_job: Tuple[Message, Job]):
                message, job = message_and_job
                if job.sample >= 1 or random.random() < job.sample:
                    await job.async_run(message)
                # Update the progress bar
                t.update()

            async with semaphore:
                # Account for the semaphore (rate limit, max_parallelism)
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Submit tasks to the executor
                    executor_results = executor.map(
                        message_job_limit_wrap, messages_and_jobs
                    )

            t.display()
            await asyncio.gather(*executor_results)
            t.close()
        elif executor_type == "sequential":
            for job_id, job in self.jobs.items():
                for one_message in tqdm(messages):
                    if job.sample >= 1 or random.random() < job.sample:
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
            for job_id, job in self.jobs.items():
                job_result = job.results.get(one_message.id, None)
                if job_result is not None:
                    results[one_message.id][job.id] = job_result

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
        for job_id, job in self.jobs.items():
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

    def run(
        self,
        messages: Iterable[Message],
        executor_type: Literal["parallel", "sequential", "parallel_jobs"] = "parallel",
        max_parallelism: int = 10,
    ):
        """
        Runs all the jobs on the message.

        Args:
        :param messages: The messages to run the jobs on.
        :param executor_type: The type of executor to use. Can be "parallel" or "sequential".
        :param max_parallelism: The maximum number of parallel jobs to run per seconds.
            Use this to adhere to rate limits. Only used if executor_type is "parallel" or "parallel_jobs".

        Returns: a mapping of message.id -> job_id -> job_result
        """

        # Run the jobs sequentially on every message
        # TODO : For Jobs, implement a batched_run method that takes a list of messages
        if executor_type == "parallel":
            for job_id, job in self.jobs.items():
                # Create a progress bar
                if hasattr(messages, "__len__"):
                    t = tqdm(total=len(messages))
                else:
                    t = tqdm()

                def job_limit_wrap(message: Message):
                    # Account for the semaphore (rate limit, max_parallelism)
                    if job.sample >= 1 or random.random() < job.sample:
                        asyncio.run(job.async_run(message))
                    # Update the progress bar
                    t.update()

                t.display()
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=max_parallelism
                ) as executor:
                    # Submit tasks to the executor
                    executor.map(job_limit_wrap, messages)

                t.close()
        elif executor_type == "parallel_jobs":
            # Create a progress bar
            if isinstance(messages, list):
                t = tqdm(total=len(messages) * len(self.jobs))
            else:
                t = tqdm()

            messages_and_jobs = itertools.product(messages, self.jobs.values())

            def message_job_limit_wrap(message_and_job: Tuple[Message, Job]):
                message, job = message_and_job
                if job.sample >= 1 or random.random() < job.sample:
                    asyncio.run(job.async_run(message))
                # Update the progress bar
                t.update()

            t.display()
            # Account for the semaphore (rate limit, max_parallelism)
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_parallelism
            ) as executor:
                # Submit tasks to the executor
                executor.map(message_job_limit_wrap, messages_and_jobs)

            t.close()
        elif executor_type == "sequential":
            for job_id, job in self.jobs.items():
                for one_message in tqdm(messages):
                    if job.sample >= 1 or random.random() < job.sample:
                        asyncio.run(job.async_run(one_message))
        else:
            raise NotImplementedError(
                f"Executor type {executor_type} is not implemented"
            )

        # Collect the results:
        # Result is a mapping of message.id -> job_id -> job_result
        results: Dict[str, Dict[str, JobResult]] = {}
        for one_message in messages:
            results[one_message.id] = {}
            for job_id, job in self.jobs.items():
                job_result = job.results.get(one_message.id, None)
                if job_result is not None:
                    results[one_message.id][job.id] = job_result

        self._results = results
        return results

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
        for job_id, job in self.jobs.items():
            job.optimize(accuracy_threshold=accuracy_threshold, min_count=min_count)

    def __repr__(self):
        concatenated_jobs = "\n".join([f"  {job}" for job in self.jobs])
        return f"Workload(jobs=[\n{concatenated_jobs}\n])"

    @property
    def results(self) -> Optional[Dict[str, Dict[str, JobResult]]]:
        if self._results is None:
            logger.warning("Results are not available. Please run the workload first.")
            return None
        # Mark all the jobs with org_id and project_id
        if self.org_id is not None or self.project_id is not None:
            for job_id, job in self.jobs.items():
                for message_id, job_result in job.results.items():
                    job_result.org_id = self.org_id
                    job_result.project_id = self.project_id
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
                    job_id: result.value
                    for job_id, result in job_results.items()
                    if result is not None
                }
                for message_id, job_results in results.items()
            },
            orient="index",
        )

        return results_df

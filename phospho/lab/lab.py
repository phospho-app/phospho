from typing import Dict, Iterable, List, Literal, Union
import yaml

import phospho.lab.job_library as job_library
import concurrent.futures


from .models import Message, JobResult


class Job:
    job_id: str
    params: dict
    job_results: Dict[str, JobResult]

    def __init__(
        self,
        job_id: str,
        job_name: str,
        params: dict,
    ):
        """
        A job is a function that takes a message and a set of parameters and returns a result.
        It stores the result.
        """
        self.job_id = job_id
        self.params = params
        # from the module .job_library import the function with the name job_name
        job_function = getattr(job_library, job_name)
        self.job_function = job_function
        # message.id -> job_result
        self.job_results: Dict[str, JobResult] = {}

    def run(self, message: Message) -> JobResult:
        """
        Run the job on the message.
        """
        result = self.job_function(message, **self.params)
        self.job_results[message.id] = result
        return result


class Laboratory:
    def __init__(self):
        """
        The Laboratory is a setup of jobs that can be run on messages.
        """
        # Read the configuration file
        with open("phospho-config.yaml") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

        # Create the jobs from the configuration
        self.jobs = []
        for job_id, job_config in self.config["jobs"].items():
            job = Job(
                job_id=job_id,
                job_name=job_config["name"],
                params=job_config["params"],
            )
            self.jobs.append(job)

    def run_experiment(
        self,
        message: Union[Message, Iterable[Message]],
        executor_type: Literal["parallel", "sequential"] = "parallel",
    ) -> Dict[str, Dict[str, JobResult]]:
        """
        Perform all the jobs on the message.

        Returns: a mapping of job_id -> message.id -> job_result
        """
        if isinstance(message, Message):
            message = [message]

        # Run all the experiments in parallel for each message
        for job in self.jobs:
            if executor_type == "parallel":
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Submit tasks to the executor
                    # executor.map(self.evaluate_a_task, task_to_evaluate)
                    executor.map(job, message)
            elif executor_type == "sequential":
                for once_message in message:
                    job(once_message)
            elif executor_type == "async":
                raise NotImplementedError(
                    f"Executor type {executor_type} is not implemented"
                )

        # Collect the results:
        # Result is a mapping of job_name -> job_result
        results = {job.job_id: job.job_results for job in self.jobs}
        return results

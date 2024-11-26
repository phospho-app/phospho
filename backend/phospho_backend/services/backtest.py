from collections.abc import Iterator
from phospho_backend.services.mongo.extractor import ExtractorClient
from phospho_backend.services.mongo.tasks import get_all_tasks
from loguru import logger
import phospho
from phospho_backend.api.v2.models import LogEvent


class BacktestLoader:
    sampled_tasks: Iterator[phospho.lab.Message] | None
    sample_size: int

    def __init__(
        self,
        project_id: str,
        filters: phospho.models.ProjectDataFilters | None = None,
    ):
        self.sampled_tasks = None
        self.project_id = project_id
        self.sample_size = 0
        self.filters = filters

    def __aiter__(self):
        return self

    async def __anext__(self) -> phospho.lab.Message:
        if self.sampled_tasks is None:
            # Fetch tasks
            tasks = await get_all_tasks(
                project_id=self.project_id, filters=self.filters
            )
            messages: list[phospho.lab.Message] = []
            for task in tasks:
                # Convert to a lab.Message
                message = phospho.lab.Message(
                    role="user",
                    content=task.input,
                    metadata={
                        "task_id": task.id,
                        "test_id": task.test_id,
                    },
                )
                messages.append(message)
            self.sample_size = len(messages)
            self.sampled_tasks = iter(messages)

        try:
            return next(self.sampled_tasks)
        except StopIteration:
            raise StopAsyncIteration

    def __len__(self) -> int:
        return self.sample_size


async def run_backtests(
    system_prompt_template: str,
    system_prompt_variables: dict,
    provider_and_model: str,
    version_id: str,
    project_id: str,
    org_id: str,
    filters: phospho.models.ProjectDataFilters,
    openai_api_key: str,
) -> None:
    # Provider verification has been done in the API endpoint

    logger.info(f"Running backtests for project {project_id}")
    provider, model = phospho.lab.get_provider_and_model(provider_and_model)
    client = phospho.lab.get_async_client(provider, api_key=openai_api_key)  # type: ignore

    all_messages = BacktestLoader(project_id=project_id, filters=filters)

    extractor_client = ExtractorClient(
        project_id=project_id,
        org_id=org_id,
    )

    async def run_model(message: phospho.lab.Message) -> str | None:
        system_prompt = system_prompt_template.format(**system_prompt_variables)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": message.role, "content": message.content},  # type: ignore
            ],
        )
        response_text = response.choices[0].message.content
        await extractor_client.run_process_log_for_tasks(
            logs_to_process=[
                LogEvent(
                    project_id=project_id,
                    input=message.content,
                    output=response_text,
                    version_id=version_id,
                    metadata={
                        "system_prompt": system_prompt,
                    },
                )
            ]
        )
        return response_text

    workload = phospho.lab.Workload(jobs=[run_model])
    workload.run(
        messages=[m async for m in all_messages],
        executor_type="parallel",
        max_parallelism=20,
    )

    return None

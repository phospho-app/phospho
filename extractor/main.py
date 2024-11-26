import asyncio
import dataclasses
import os

import aiohealthcheck  # type: ignore
import sentry_sdk
from loguru import logger
from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)

from extractor.core import config
from extractor.db.mongo import close_mongo_db, connect_and_init_db
from extractor.sentry.interceptor import SentryInterceptor
from extractor.temporal.activities import (
    bill_on_stripe,
    extract_langfuse_data,
    extract_langsmith_data,
    run_main_pipeline_on_messages,
    run_main_pipeline_on_task,
    run_process_logs_for_messages,
    run_process_logs_for_tasks,
    run_process_tasks,
    run_recipe_on_task,
)
from extractor.temporal.pydantic_converter import pydantic_data_converter
from extractor.temporal.workflows import (
    ExtractLangfuseDataWorkflow,
    ExtractLangSmithDataWorkflow,
    RunMainPipelineOnMessagesWorkflow,
    RunMainPipelineOnTaskWorkflow,
    RunProcessLogsForMessagesWorkflow,
    RunProcessLogsForTasksWorkflow,
    RunProcessTasksWorkflow,
    RunRecipeOnTaskWorkflow,
)

logger.info("Starting worker")


# Due to known issues with Pydantic's use of issubclass and our inability to
# override the check in sandbox, Pydantic will think datetime is actually date
# in the sandbox. At the expense of protecting against datetime.now() use in
# workflows, we're going to remove datetime module restrictions. See sdk-python
# README's discussion of known sandbox issues for more details.
def new_sandbox_runner() -> SandboxedWorkflowRunner:
    # TODO(cretz): Use with_child_unrestricted when https://github.com/temporalio/sdk-python/issues/254
    # is fixed and released
    invalid_module_member_children = dict(
        SandboxRestrictions.invalid_module_members_default.children
    )
    del invalid_module_member_children["datetime"]
    return SandboxedWorkflowRunner(
        restrictions=dataclasses.replace(
            SandboxRestrictions.default,
            invalid_module_members=dataclasses.replace(
                SandboxRestrictions.invalid_module_members_default,
                children=invalid_module_member_children,
            ),
        )
    )


interrupt_event = asyncio.Event()


async def main() -> None:
    if config.ENVIRONMENT in ["production", "staging"]:
        sentry_sdk.init(
            dsn=os.getenv("EXTRACTOR_SENTRY_DSN"),
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )
        sentry_sdk.set_level("warning")

    await connect_and_init_db()

    client: Client
    if config.ENVIRONMENT in ["production", "staging"]:
        client_cert = config.TEMPORAL_MTLS_TLS_CERT
        client_key = config.TEMPORAL_MTLS_TLS_KEY

        client = await Client.connect(
            config.TEMPORAL_HOST_URL,  # type: ignore
            namespace=config.TEMPORAL_NAMESPACE,  # type: ignore
            tls=TLSConfig(
                client_cert=client_cert,
                client_private_key=client_key,
            ),
            data_converter=pydantic_data_converter,
        )
    elif config.ENVIRONMENT in ["test", "preview"]:
        try:
            client = await Client.connect(
                config.TEMPORAL_HOST_URL,  # type: ignore
                namespace=config.TEMPORAL_NAMESPACE,  # type: ignore
                tls=False,
                data_converter=pydantic_data_converter,
            )
        except Exception as e:
            logger.error("Have you started a local Temporal server?")
            logger.error(f"Error connecting to Temporal: {e}")
            raise e
    else:
        raise ValueError(f"Unknown environment {config.ENVIRONMENT}")

    async with Worker(
        client,
        task_queue="default",
        workflows=[  # We add workflows that our worker can process here
            ExtractLangSmithDataWorkflow,
            ExtractLangfuseDataWorkflow,
            RunRecipeOnTaskWorkflow,
            RunProcessLogsForTasksWorkflow,
            RunMainPipelineOnMessagesWorkflow,
            RunMainPipelineOnTaskWorkflow,
            RunProcessTasksWorkflow,
            RunProcessLogsForMessagesWorkflow,
        ],
        activities=[  # And the linked activities here
            extract_langsmith_data,
            extract_langfuse_data,
            run_recipe_on_task,
            bill_on_stripe,
            run_main_pipeline_on_messages,
            run_main_pipeline_on_task,
            run_process_tasks,
            run_process_logs_for_tasks,
            run_process_logs_for_messages,
        ],
        workflow_runner=new_sandbox_runner(),
        interceptors=[SentryInterceptor()]
        if config.ENVIRONMENT in ["production", "staging"]
        else [],
        identity="extractor-worker",
    ):
        logger.info("Worker started")
        await interrupt_event.wait()
        await close_mongo_db()
        logger.info("Shutting down")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        if config.ENVIRONMENT in ["production", "staging"]:
            # Perform a health check on the worker (only in production/staging)
            loop.create_task(aiohealthcheck.tcp_health_endpoint(port=8080))
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

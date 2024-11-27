import asyncio
import dataclasses
import os

import aiohealthcheck  # type: ignore
import sentry_sdk
from ai_hub.core import config  # Also load the .env file
from ai_hub.db.mongo import (
    close_mongo_db,
    connect_and_init_db,
)
from ai_hub.sentry.interceptor import SentryInterceptor
from ai_hub.temporal.activities import (
    bill_on_stripe,
    create_embeddings,
    generate_clustering,
)
from ai_hub.temporal.pydantic_converter import pydantic_data_converter
from ai_hub.temporal.workflows import (
    CreateEmbeddingsWorkflow,
    GenerateClusteringWorkflow,
)
from loguru import logger
from temporalio.client import Client, TLSConfig
from temporalio.worker import Worker
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
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


async def main():
    if config.ENVIRONMENT in ["production", "staging"]:
        sentry_sdk.init(
            dsn=os.getenv("EXTRACTOR_SENTRY_DSN"),
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )
        sentry_sdk.set_level("warning")

    await connect_and_init_db()

    if config.ENVIRONMENT in ["production", "staging"]:
        client_cert = config.TEMPORAL_MTLS_TLS_CERT
        client_key = config.TEMPORAL_MTLS_TLS_KEY

        client: Client = await Client.connect(
            os.getenv("TEMPORAL_HOST_URL"),
            namespace=os.getenv("TEMPORAL_NAMESPACE"),
            tls=TLSConfig(
                client_cert=client_cert,
                client_private_key=client_key,
            ),
            data_converter=pydantic_data_converter,
        )
    elif config.ENVIRONMENT in ["test", "preview"]:
        logger.debug("Connecting to Temporal without TLS")
        client: Client = await Client.connect(
            os.getenv("TEMPORAL_HOST_URL"),
            namespace=os.getenv("TEMPORAL_NAMESPACE"),
            tls=False,
            data_converter=pydantic_data_converter,
        )
    else:
        client: Client = None
        raise ValueError(f"Unknown environment {config.ENVIRONMENT}")

    async with Worker(
        client,
        task_queue="ai-hub",
        workflows=[  # We add workflows that our worker can process here
            CreateEmbeddingsWorkflow,
            GenerateClusteringWorkflow,
        ],
        activities=[  # And the linked activities here
            create_embeddings,
            generate_clustering,
            bill_on_stripe,
        ],
        workflow_runner=new_sandbox_runner(),
        interceptors=[SentryInterceptor()]
        if config.ENVIRONMENT == "production" or config.ENVIRONMENT == "staging"
        else [],
        identity="ai-hub-worker",
    ):
        logger.info("Worker started")
        await interrupt_event.wait()
        await close_mongo_db()
        logger.info("Shutting down")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        if config.ENVIRONMENT in ["production", "staging"]:
            # The health is only checked in production and staging
            loop.create_task(aiohealthcheck.tcp_health_endpoint(port=8081))
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

"""
This module contains the Temporal workflows for the extractor service.

Few things to note:
- The workflows are defined as classes with the `@workflow.defn` decorator.
- The `@workflow.run` decorator is used to define the `run` method of the class.
- The `run` method is used to run the activity associated with the workflow.
- The `run` method of the class calls the `run_activity` method of the parent class.
- The `run_activity` method of the parent class runs the activity associated with the workflow.
- The `run_activity` method also bills the customer for the activity if the `bill` attribute of the class is set to `True`.

To consider:
- When sending a workflow from the backend, we must also send the customer_id, org_id, and project_id to bill the customer.
"""

import traceback
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    import asyncio
    import threading

    import httpx
    import sentry_sdk
    import sniffio
    import stripe
    from ai_hub.core import config
    from ai_hub.models.clusterings import ClusteringRequest
    from ai_hub.models.embeddings import EmbeddingRequest
    from ai_hub.models.stripe import BillOnStripeRequest
    from ai_hub.temporal.activities import (
        bill_on_stripe,
        create_embeddings,
        generate_clustering,
    )
    from loguru import logger


class BaseWorkflow:
    def __init__(
        self,
        activity_func,
        request_class,
        bill=True,
        max_retries=1,
    ):
        self.activity_func = activity_func
        self.request_class = request_class
        self.bill = bill
        self.max_retries = max_retries

    async def run_activity(self, request):
        retry_policy = RetryPolicy(
            maximum_attempts=self.max_retries,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )
        request = self.request_class(**request)
        await workflow.execute_activity(
            self.activity_func,
            request,
            start_to_close_timeout=timedelta(minutes=120),
            retry_policy=retry_policy,
        )
        if self.bill:
            logger.debug(
                f"Running activity {self.activity_func.__name__} with request {request}"
            )
            await workflow.execute_activity(
                bill_on_stripe,
                BillOnStripeRequest(
                    org_id=request.org_id,
                    project_id=request.project_id,
                    nb_credits_used=request.nb_credits_used,
                    customer_id=request.customer_id,
                ),
                start_to_close_timeout=timedelta(minutes=1),
            )


@workflow.defn(name="create_embeddings_workflow")
class CreateEmbeddingsWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            activity_func=create_embeddings,
            request_class=EmbeddingRequest,
            bill=False,  # For now, we bill in the backend
        )

    @workflow.run
    async def run_activity(self, request):
        return await super().run_activity(request)


@workflow.defn(name="generate_clustering_workflow")
class GenerateClusteringWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            activity_func=generate_clustering,
            request_class=ClusteringRequest,
        )

    @workflow.run
    async def run_activity(self, request):
        return await super().run_activity(request)

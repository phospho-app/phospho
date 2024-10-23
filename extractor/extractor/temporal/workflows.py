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
from typing import Any, Callable, Type
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    import stripe
    import asyncio
    import httpx
    import threading
    import sentry_sdk
    from loguru import logger
    from extractor.core import config
    from extractor.services.slack import slack_notification
    from extractor.services.pipelines import MainPipeline
    from extractor.services.connectors import (
        LangsmithConnector,
        LangfuseConnector,
        OpenTelemetryConnector,
    )
    from extractor.services.projects import get_project_by_id
    from extractor.temporal.activities import (
        extract_langsmith_data,
        extract_langfuse_data,
        store_open_telemetry_data,
        run_recipe_on_task,
        run_process_tasks,
        run_main_pipeline_on_messages,
        run_main_pipeline_on_task,
        bill_on_stripe,
        run_process_logs_for_tasks,
    )
    from extractor.models.log import (
        LogProcessRequestForMessages,
        TaskProcessRequest,
        LogProcessRequestForTasks,
    )
    from extractor.models.pipelines import (
        PipelineLangfuseRequest,
        PipelineLangsmithRequest,
        PipelineOpentelemetryRequest,
        PipelineResults,
        RunMainPipelineOnMessagesRequest,
        RunMainPipelineOnTaskRequest,
        RunRecipeOnTaskRequest,
        BillOnStripeRequest,
        ExtractorBaseClass,
    )


class BaseWorkflow:
    def __init__(
        self,
        activity_func: Callable[[Any], dict],
        request_class: Type[ExtractorBaseClass],
        bill: bool = True,
        max_retries: int = 1,
    ):
        self.activity_func = activity_func
        self.request_class = request_class
        self.bill = bill
        self.max_retries = max_retries
        self.retry_policy = RetryPolicy(
            maximum_attempts=self.max_retries,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )

    async def run_activity(self, request: dict) -> None:
        request_model = self.request_class(**request)
        response = await workflow.execute_activity(
            self.activity_func,
            request,
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=self.retry_policy,
        )
        if self.bill:
            await workflow.execute_activity(
                bill_on_stripe,
                BillOnStripeRequest(
                    org_id=request_model.org_id,
                    project_id=request_model.project_id,
                    nb_job_results=response.get("nb_job_results", 0),
                    customer_id=request_model.customer_id,
                    current_usage=request_model.current_usage,
                    max_usage=request_model.max_usage,
                    recipe_type=response.get("recipe_type", None),
                ),
                start_to_close_timeout=timedelta(minutes=1),
            )


@workflow.defn(name="extract_langsmith_data_workflow")
class ExtractLangSmithDataWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            activity_func=extract_langsmith_data,
            request_class=PipelineLangsmithRequest,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="extract_langfuse_data_workflow")
class ExtractLangfuseDataWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            activity_func=extract_langfuse_data,
            request_class=PipelineLangfuseRequest,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="store_open_telemetry_data_workflow")
class StoreOpenTelemetryDataWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            activity_func=store_open_telemetry_data,
            request_class=PipelineOpentelemetryRequest,
            bill=False,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="run_recipe_on_task_workflow")
class RunRecipeOnTaskWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            activity_func=run_recipe_on_task,
            request_class=RunRecipeOnTaskRequest,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="run_process_tasks_workflow")
class RunProcessTasksWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            activity_func=run_process_tasks,
            request_class=TaskProcessRequest,
            max_retries=2,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="run_process_logs_for_tasks_workflow")
class RunProcessLogsForTasksWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            activity_func=run_process_logs_for_tasks,
            request_class=LogProcessRequestForTasks,
            max_retries=2,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="run_main_pipeline_on_messages_workflow")
class RunMainPipelineOnMessagesWorkflow:
    def __init__(self):
        self.retry_policy = RetryPolicy(
            maximum_attempts=2,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )

    @workflow.run
    async def run(
        self, request: RunMainPipelineOnMessagesRequest
    ) -> PipelineResults | None:
        response = await workflow.execute_activity(
            run_main_pipeline_on_messages,
            request,
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=self.retry_policy,
        )
        await workflow.execute_activity(
            bill_on_stripe,
            BillOnStripeRequest(
                org_id=request.org_id,
                project_id=request.project_id,
                nb_job_results=len(request.messages) if response is not None else 0,
                customer_id=request.customer_id,
                current_usage=request.current_usage,
                max_usage=request.max_usage,
                recipe_type=None,
            ),
            start_to_close_timeout=timedelta(minutes=1),
        )
        return response


@workflow.defn(name="run_main_pipeline_on_task_workflow")
class RunMainPipelineOnTaskWorkflow:
    def __init__(self):
        self.retry_policy = RetryPolicy(
            maximum_attempts=2,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )

    @workflow.run
    async def run(
        self, request: RunMainPipelineOnTaskRequest
    ) -> PipelineResults | None:
        response = await workflow.execute_activity(
            run_main_pipeline_on_task,
            request,
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=self.retry_policy,
        )
        await workflow.execute_activity(
            bill_on_stripe,
            BillOnStripeRequest(
                org_id=request.org_id,
                project_id=request.project_id,
                nb_job_results=1 if response is not None else 0,
                customer_id=request.customer_id,
                current_usage=request.current_usage,
                max_usage=request.max_usage,
                recipe_type=None,
            ),
            start_to_close_timeout=timedelta(minutes=1),
        )
        return response

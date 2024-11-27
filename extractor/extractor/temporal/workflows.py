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
    import asyncio
    import threading

    import httpx
    import sentry_sdk
    import stripe
    from loguru import logger

    from extractor.core import config
    from extractor.models.log import (
        LogProcessRequestForMessages,
        LogProcessRequestForTasks,
        TaskProcessRequest,
    )
    from extractor.models.pipelines import (
        BillOnStripeRequest,
        ExtractorBaseClass,
        PipelineLangfuseRequest,
        PipelineLangsmithRequest,
        PipelineResults,
        RunMainPipelineOnMessagesRequest,
        RunMainPipelineOnTaskRequest,
        RunRecipeOnTaskRequest,
    )
    from extractor.services.connectors import (
        LangfuseConnector,
        LangsmithConnector,
    )
    from extractor.services.pipelines import MainPipeline
    from extractor.services.projects import get_project_by_id
    from extractor.services.slack import slack_notification
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
        logger.info(f"Running run_process_tasks_workflow with request: {request}")
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
        logger.info(
            f"Running run_process_logs_for_tasks_workflow with request: {request}"
        )
        await super().run_activity(request)


@workflow.defn(name="run_process_logs_for_messages_workflow")
class RunProcessLogsForMessagesWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            activity_func=run_process_logs_for_messages,
            request_class=LogProcessRequestForMessages,
            max_retries=2,
        )

    @workflow.run
    async def run(self, request):
        logger.info(
            f"Running run_process_logs_for_messages_workflow with request: {request}"
        )
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

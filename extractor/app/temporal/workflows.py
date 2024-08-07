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
    from app.temporal.activities import (
        extract_langsmith_data,
        extract_langfuse_data,
        store_open_telemetry_data,
        run_recipe_on_task,
        run_process_logs_for_messages,
        run_process_log_for_tasks,
        run_main_pipeline_on_messages,
        bill_on_stripe,
    )
    from app.api.v1.models import (
        PipelineLangfuseRequest,
        PipelineLangsmithRequest,
        PipelineOpentelemetryRequest,
        RunMainPipelineOnMessagesRequest,
        RunRecipeOnTaskRequest,
        LogProcessRequestForMessages,
        LogProcessRequestForTasks,
        BillOnStripeRequest,
    )
    from loguru import logger
    from app.core import config
    from app.services.slack import slack_notification


class BaseWorkflow:
    def __init__(
        self,
        name,
        activity_func,
        request_class,
        bill=True,
    ):
        self.name = name
        self.activity_func = activity_func
        self.request_class = request_class
        self.bill = bill

    async def run_activity(self, request):
        retry_policy = RetryPolicy(
            maximum_attempts=1,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )
        try:
            request = self.request_class(**request)
            response = await workflow.execute_activity(
                self.activity_func,
                request,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=retry_policy,
            )
            if self.bill:
                await workflow.execute_activity(
                    bill_on_stripe,
                    BillOnStripeRequest(
                        org_id=request.org_id,
                        project_id=request.project_id,
                        nb_job_results=response.get("nb_job_results", 0),
                        customer_id=request.customer_id,
                    ),
                    start_to_close_timeout=timedelta(minutes=1),
                )
        except Exception as e:
            error_message = f"Caught error while calling temporal workflow {self.name}: {e}\n{traceback.format_exception(e)}"
            logger.error(f"Error in {self.name}: {e}")
            if config.ENVIRONMENT in ["production", "staging"]:
                slack_message = (
                    error_message[:300] if len(error_message) > 300 else error_message
                )
                await slack_notification(slack_message)


@workflow.defn(name="extract_langsmith_data_workflow")
class extract_langsmith_data_workflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            name="extract_langsmith_data_workflow",
            activity_func=extract_langsmith_data,
            request_class=PipelineLangsmithRequest,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="extract_langfuse_data_workflow")
class extract_langfuse_data_workflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            name="extract_langfuse_data_workflow",
            activity_func=extract_langfuse_data,
            request_class=PipelineLangfuseRequest,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="store_open_telemetry_data_workflow")
class store_open_telemetry_data_workflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            name="store_open_telemetry_data_workflow",
            activity_func=store_open_telemetry_data,
            request_class=PipelineOpentelemetryRequest,
            bill=False,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="run_recipe_on_task_workflow")
class run_recipe_on_task_workflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            name="run_recipe_on_task_workflow",
            activity_func=run_recipe_on_task,
            request_class=RunRecipeOnTaskRequest,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="run_main_pipeline_on_messages_workflow")
class run_main_pipeline_on_messages_workflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            name="run_main_pipeline_on_messages_workflow",
            activity_func=run_main_pipeline_on_messages,
            request_class=RunMainPipelineOnMessagesRequest,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="run_process_logs_for_messages_workflow")
class run_process_logs_for_messages_workflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            name="run_process_logs_for_messages_workflow",
            activity_func=run_process_logs_for_messages,
            request_class=LogProcessRequestForMessages,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)


@workflow.defn(name="run_process_log_for_tasks_workflow")
class run_process_log_for_tasks_workflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            name="run_process_log_for_tasks_workflow",
            activity_func=run_process_log_for_tasks,
            request_class=LogProcessRequestForTasks,
        )

    @workflow.run
    async def run(self, request):
        await super().run_activity(request)

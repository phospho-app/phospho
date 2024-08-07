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


@workflow.defn(name="extract_langsmith_data_workflow")
class extract_langsmith_data_workflow:
    @workflow.run
    async def run(self, request: PipelineLangsmithRequest):
        """
        Extracts data from LangSmith through its python package, stores and processes the data, then bills the organization.
        """
        retry_policy = RetryPolicy(
            maximum_attempts=1,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )
        try:
            response = await workflow.execute_activity(
                extract_langsmith_data,
                request,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=retry_policy,
            )
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
            error_message = f"Caught error while calling temporal workflow extract_langsmith_data_workflow: {e}\n{traceback.format_exception(e)}"
            logger.error(f"Error in extract_langsmith_data_workflow: {e}")
            if config.ENVIRONMENT in ["production", "staging"]:
                if len(error_message) > 300:
                    slack_message = error_message[:300]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)


@workflow.defn(name="extract_langfuse_data_workflow")
class extract_langfuse_data_workflow:
    @workflow.run
    async def run(self, request: PipelineLangfuseRequest):
        """
        Extracts data from LangFuse through its python package, stores and processes the data, then bills the organization.
        """
        retry_policy = RetryPolicy(
            maximum_attempts=1,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )
        try:
            response = await workflow.execute_activity(
                extract_langfuse_data,
                request,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=retry_policy,
            )
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
            error_message = f"Caught error while calling temporal workflow extract_langfuse_data_workflow: {e}\n{traceback.format_exception(e)}"
            logger.error(f"Error in extract_langfuse_data_workflow: {e}")
            if config.ENVIRONMENT in ["production", "staging"]:
                if len(error_message) > 300:
                    slack_message = error_message[:300]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)


@workflow.defn(name="store_open_telemetry_data_workflow")
class store_open_telemetry_data_workflow:
    @workflow.run
    async def run(self, request: PipelineOpentelemetryRequest):
        """
        Stores open telemetry logs without handling them.
        """
        retry_policy = RetryPolicy(
            maximum_attempts=1,
            maximum_interval=timedelta(minutes=2),
            non_retryable_error_types=["ValueError"],
        )
        return await workflow.execute_activity(
            store_open_telemetry_data,
            request,
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy,
        )


@workflow.defn(name="run_recipe_on_task_workflow")
class run_recipe_on_task_workflow:
    @workflow.run
    async def run(self, request: RunRecipeOnTaskRequest):
        """
        Runs a recipe on tasks, then bills the organization.
        Used to run the main pipeline on past data.
        """
        retry_policy = RetryPolicy(
            maximum_attempts=1,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )
        try:
            response = await workflow.execute_activity(
                run_recipe_on_task,
                request,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=retry_policy,
            )
            if len(request.tasks) > 0:
                await workflow.execute_activity(
                    bill_on_stripe,
                    BillOnStripeRequest(
                        org_id=request.recipe.org_id,
                        project_id=request.tasks[0].project_id,
                        nb_job_results=response.get("nb_job_results", 0),
                        customer_id=request.customer_id,
                    ),
                    start_to_close_timeout=timedelta(minutes=1),
                )
        except Exception as e:
            error_message = f"Caught error while calling temporal workflow run_recipe_on_task_workflow: {e}\n{traceback.format_exception(e)}"
            logger.error(f"Error in run_recipe_on_task_workflow: {e}")
            if config.ENVIRONMENT in ["production", "staging"]:
                if len(error_message) > 300:
                    slack_message = error_message[:300]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)


@workflow.defn(name="run_main_pipeline_on_messages_workflow")
class run_main_pipeline_on_messages_workflow:
    @workflow.run
    async def run(self, request: RunMainPipelineOnMessagesRequest):
        retry_policy = RetryPolicy(
            maximum_attempts=1,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )
        try:
            await workflow.execute_activity(
                run_main_pipeline_on_messages,
                request,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=retry_policy,
            )
            await workflow.execute_activity(
                bill_on_stripe,
                BillOnStripeRequest(
                    org_id=request.org_id,
                    nb_job_results=1,
                    customer_id=request.customer_id,
                ),
                start_to_close_timeout=timedelta(minutes=1),
            )
        except Exception as e:
            error_message = f"Caught error while calling temporal workflow run_main_pipeline_on_messages_workflow: {e}\n{traceback.format_exception(e)}"
            logger.error(f"Error in run_main_pipeline_on_messages_workflow: {e}")
            if config.ENVIRONMENT in ["production", "staging"]:
                if len(error_message) > 300:
                    slack_message = error_message[:300]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)


@workflow.defn(name="run_process_logs_for_messages_workflow")
class run_process_logs_for_messages_workflow:
    @workflow.run
    async def run(self, request: LogProcessRequestForMessages):
        retry_policy = RetryPolicy(
            maximum_attempts=1,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )
        try:
            response = await workflow.execute_activity(
                run_process_logs_for_messages,
                request,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=retry_policy,
            )
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
            error_message = f"Caught error while calling temporal workflow post_log_messages_workflow: {e}\n{traceback.format_exception(e)}"
            logger.error(f"Error in post_log_messages_workflow: {e}")
            if config.ENVIRONMENT in ["production", "staging"]:
                if len(error_message) > 300:
                    slack_message = error_message[:300]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)


@workflow.defn(name="run_process_log_for_tasks_workflow")
class run_process_log_for_tasks_workflow:
    """
    Run the log procesing pipeline for tasks.
    Saves logs, creates tasks and sessions and triggers the main pipeline.
    """

    @workflow.run
    async def run(self, request: LogProcessRequestForTasks):
        logger.info(
            f"Processing {len(request.logs_to_process)} logs and saving {len(request.extra_logs_to_save)} extra logs."
        )
        retry_policy = RetryPolicy(
            maximum_attempts=1,
            maximum_interval=timedelta(minutes=5),
            non_retryable_error_types=["ValueError"],
        )
        try:
            response = await workflow.execute_activity(
                run_process_log_for_tasks,
                request,
                start_to_close_timeout=timedelta(minutes=15),
                retry_policy=retry_policy,
            )
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
            error_message = f"Caught error while calling temporal workflow run_process_log_for_tasks_workflow: {e}\n{traceback.format_exception(e)}"
            logger.error(f"Error in run_process_log_for_tasks_workflow: {e}")
            if config.ENVIRONMENT in ["production", "staging"]:
                if len(error_message) > 300:
                    slack_message = error_message[:300]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)

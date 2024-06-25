# Models
from app.db.mongo import get_mongo_db
from app.api.v1.models import (
    LogProcessRequest,
    PipelineResults,
    RunMainPipelineOnMessagesRequest,
    RunMainPipelineOnTaskRequest,
    RunRecipeOnTaskRequest,
    AugmentedOpenTelemetryData,
)

# Security
from app.security.authentication import authenticate_key
from app.services.log import process_log

# Services
from app.services.pipelines import (
    messages_main_pipeline,
    recipe_pipeline,
    task_main_pipeline,
    store_opentelemetry_data_in_db,
    get_last_langsmith_extract,
    get_last_langfuse_extract,
    change_last_langsmith_extract,
    encrypt_and_store_langsmith_credentials,
    task_scoring_pipeline,
    change_last_langfuse_extract,
    encrypt_and_store_langfuse_credentials,
)
from app.services.projects import get_project_by_id
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from app.api.v1.models import LogEvent
from datetime import datetime
from langsmith import Client
from langfuse import Langfuse
from typing import List

router = APIRouter()


@router.post(
    "/pipelines/main/task",
    description="Main extractor pipeline",
    response_model=PipelineResults,
)
async def post_main_pipeline_on_task(
    request_body: RunMainPipelineOnTaskRequest,
    is_request_authenticated: bool = Depends(authenticate_key),
) -> PipelineResults:
    logger.debug(f"task: {request_body.task}")
    pipeline_results = await task_main_pipeline(
        task=request_body.task,
        save_task=request_body.save_results,
    )
    return pipeline_results


@router.post(
    "/pipelines/eval/task",
    description="Eval extractor pipeline",
    response_model=PipelineResults,
)
async def post_eval_pipeline_on_task(
    request_body: RunMainPipelineOnTaskRequest,
    is_request_authenticated: bool = Depends(authenticate_key),
) -> PipelineResults:
    logger.debug(f"task: {request_body.task}")
    # Do the session scoring -> success, failure
    mongo_db = await get_mongo_db()

    if request_body.save_results:
        task_in_db = await mongo_db["tasks"].find_one({"id": request_body.task.id})
        if task_in_db.get("flag") is None:
            flag = await task_scoring_pipeline(
                request_body.task, save_task=request_body.save_results
            )
        else:
            flag = task_in_db.get("flag")
    else:
        flag = await task_scoring_pipeline(
            request_body.task, save_task=request_body.save_results
        )

    pipeline_results = PipelineResults(
        events=[],
        flag=flag,
        language=None,
        sentiment=None,
    )

    return pipeline_results


@router.post(
    "/pipelines/main/messages",
    description="Main extractor pipeline on messages",
    response_model=PipelineResults,
)
async def post_main_pipeline_on_messages(
    request_body: RunMainPipelineOnMessagesRequest,
    is_request_authenticated: bool = Depends(authenticate_key),
) -> PipelineResults:
    pipeline_results = await messages_main_pipeline(
        project_id=request_body.project_id,
        messages=request_body.messages,
    )
    return pipeline_results


@router.post(
    "/pipelines/log",
    description="Store a batch of log events in database",
)
async def post_log(
    request_body: LogProcessRequest,
    background_tasks: BackgroundTasks,
    is_request_authenticated: bool = Depends(authenticate_key),
):
    if is_request_authenticated:
        logger.info(
            f"Project {request_body.project_id} org {request_body.org_id}: processing {len(request_body.logs_to_process)} logs and saving {len(request_body.extra_logs_to_save)} extra logs."
        )
        background_tasks.add_task(
            process_log,
            project_id=request_body.project_id,
            org_id=request_body.org_id,
            logs_to_process=request_body.logs_to_process,
            extra_logs_to_save=request_body.extra_logs_to_save,
        )

        project = await get_project_by_id(request_body.project_id)
        nbr_event = len(project.settings.events)

        # We return the number of events to process + 2 (one for the eval and one for the sentiment analysis)
        return {
            "status": "ok",
            "nb_job_results": len(request_body.logs_to_process) * (nbr_event + 2),
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post(
    "/pipelines/recipes",
    description="Run a recipe on tasks",
)
async def post_run_job_on_task(
    request: RunRecipeOnTaskRequest,
    background_tasks: BackgroundTasks,
    is_request_authenticated: bool = Depends(authenticate_key),
):
    # If there are no tasks to process, return
    if len(request.tasks) == 0:
        logger.debug("No tasks to process.")
        return {"status": "no tasks to process", "nb_job_results": 0}
    # Run the valid recipes
    logger.info(
        f"Running job {request.recipe.recipe_type} on {len(request.tasks)} tasks."
    )
    background_tasks.add_task(
        recipe_pipeline,
        tasks=request.tasks,
        recipe=request.recipe,
    )
    return {"status": "ok", "nb_job_results": len(request.tasks)}


@router.post(
    "/pipelines/opentelemetry",
    response_model=dict,
    description="Store data from OpenTelemetry in database",
)
async def store_opentelemetry_data(
    augmented_open_telemetry_data: AugmentedOpenTelemetryData,
    background_tasks: BackgroundTasks,
) -> dict:
    """Store the opentelemetry data in the opentelemetry database"""

    logger.debug(
        f"Storing opentelemetry data for project {augmented_open_telemetry_data.project_id}"
    )

    try:
        # Assuming the JSON is stored in a variable called 'json_data'
        data = augmented_open_telemetry_data.open_telemetry_data

        # TODO: Find better way of doing this
        resource_spans = data["resourceSpans"]
        resource = resource_spans[0]["scopeSpans"]
        spans = resource[0]["spans"][0]

        # Unpack attributes
        attributes = spans["attributes"]
        unpacked_attributes = {}
        for attr in attributes:
            k = attr["key"]

            if "stringValue" in attr["value"]:
                value = attr["value"]["stringValue"]
            elif "intValue" in attr["value"]:
                value = attr["value"]["intValue"]
            elif "boolValue" in attr["value"]:
                value = attr["value"]["boolValue"]
            elif "doubleValue" in attr["value"]:
                value = attr["value"]["doubleValue"]
            elif "arrayValue" in attr["value"]:
                value = attr["value"]["arrayValue"]
            else:
                logger.error(f"Unknown value type: {attr['value']}")
                continue

            keys = k.split(".")
            current_dict = unpacked_attributes
            for i, key in enumerate(keys[:-1]):
                if key.isdigit():
                    # Skip if key is a digit: No need to unpack
                    continue

                # Initialize the key if it does not exist
                if key not in current_dict:
                    if keys[i + 1].isdigit():
                        # If next key is a digit, then current key is a list
                        current_dict[key] = []
                    else:
                        # If next key is not a digit, then current key is a dictionary
                        current_dict[key] = {}

                # Move to the next level
                if keys[i + 1].isdigit():
                    # If next key is a digit, then the current key is a list
                    if len(current_dict[key]) < int(keys[i + 1]) + 1:
                        current_dict[key].append({})
                    try:
                        current_dict = current_dict[key][int(keys[i + 1])]
                    except IndexError:
                        logger.error(
                            f"IndexError: {key} {keys[i + 1]} {current_dict[key]}"
                        )
                        continue
                else:
                    current_dict = current_dict[key]
            current_dict[keys[-1]] = value

        spans["attributes"] = unpacked_attributes

        logger.debug(f"Unpacked attributes: {unpacked_attributes}")

        # We only keep the spans that have the "gen_ai.system" attribute
        if "gen_ai" in unpacked_attributes:
            background_tasks.add_task(
                store_opentelemetry_data_in_db,
                open_telemetry_data=spans,
                project_id=augmented_open_telemetry_data.project_id,
                org_id=augmented_open_telemetry_data.org_id,
            )

        return {"status": "ok"}

    except KeyError as e:
        logger.error(f"KeyError: {e}")
        return {"status": "error", "message": f"KeyError: {e}"}


@router.post(
    "/pipelines/langsmith",
    description="Run the langsmith pipeline on a task",
)
async def extract_langsmith_data(
    user_data: dict,
    background_tasks: BackgroundTasks,
):
    logger.debug(
        f"Received Langsmith connection data for org id: {user_data['org_id']}, {user_data}"
    )

    last_langsmith_extract = await get_last_langsmith_extract(user_data["project_id"])

    client = Client(api_key=user_data["langsmith_credentials"]["langsmith_api_key"])
    if last_langsmith_extract is None:
        runs = client.list_runs(
            project_name=user_data["langsmith_credentials"]["project_name"],
            run_type="llm",
        )

    else:
        runs = client.list_runs(
            project_name=user_data["langsmith_credentials"]["project_name"],
            run_type="llm",
            start_time=datetime.strptime(
                last_langsmith_extract, "%Y-%m-%d %H:%M:%S.%f"
            ),
        )

    logs_to_process: List[LogEvent] = []
    extra_logs_to_save: List[LogEvent] = []
    current_usage = user_data["current_usage"]
    max_usage = user_data["max_usage"]

    for run in runs:
        try:
            input = ""
            for message in run.inputs["messages"]:
                if "HumanMessage" in message["id"]:
                    input += message["kwargs"]["content"]

            output = ""
            for generation in run.outputs["generations"]:
                output += generation["text"]

            if input == "" or output == "":
                continue

            log_event = LogEvent(
                created_at=str(int(run.end_time.timestamp())),
                input=input,
                output=output,
                session_id=str(run.session_id),
                org_id=user_data["org_id"],
                project_id=user_data["project_id"],
                metadata={"langsmith_run_id": run.id},
            )

            if max_usage is None or (
                max_usage is not None and current_usage < max_usage
            ):
                logs_to_process.append(log_event)
                current_usage += 1
            else:
                extra_logs_to_save.append(log_event)
        except Exception as e:
            logger.error(
                f"Error processing langsmith run for project id: {user_data['project_id']}, {e}"
            )

    await change_last_langsmith_extract(
        project_id=user_data["project_id"],
        new_last_extract_date=str(datetime.now()),
    )

    background_tasks.add_task(
        process_log,
        project_id=user_data["project_id"],
        org_id=user_data["org_id"],
        logs_to_process=logs_to_process,
        extra_logs_to_save=extra_logs_to_save,
    )

    logger.debug(
        f"Finished processing langsmith runs for project id: {user_data['project_id']}"
    )

    await encrypt_and_store_langsmith_credentials(
        project_id=user_data["project_id"],
        langsmith_api_key=user_data["langsmith_credentials"]["langsmith_api_key"],
        langsmith_project_name=user_data["langsmith_credentials"]["project_name"],
    )

    return {"status": "ok"}


@router.post(
    "/pipelines/langfuse",
    description="Run the langfuse pipeline on a task",
)
async def extract_langfuse_data(
    user_data: dict,
    background_tasks: BackgroundTasks,
):
    logger.debug(f"Received LangFuse connection data for org id: {user_data['org_id']}")

    last_langfuse_extract = await get_last_langfuse_extract(user_data["project_id"])

    langfuse = Langfuse(
        public_key=user_data["langfuse_credentials"]["langfuse_public_key"],
        secret_key=user_data["langfuse_credentials"]["langfuse_secret_key"],
    )

    if last_langfuse_extract is None:
        observations = langfuse.client.observations.get_many(type="GENERATION")

    else:
        observations = langfuse.client.observations.get_many(
            type="GENERATION",
            from_start_time=datetime.strptime(
                last_langfuse_extract, "%Y-%m-%d %H:%M:%S.%f"
            ),
        )

    logs_to_process: List[LogEvent] = []
    extra_logs_to_save: List[LogEvent] = []
    current_usage = user_data["current_usage"]
    max_usage = user_data["max_usage"]

    for observation in observations.data:
        try:
            input = observation.input
            output = observation.output

            log_event = LogEvent(
                created_at=str(int(observation.start_time.timestamp())),
                input=input,
                output=output,
                session_id=str(observation.trace_id),
                org_id=user_data["org_id"],
                project_id=user_data["project_id"],
                metadata={"langsfuse_run_id": observation.id},
            )

            if max_usage is None or (
                max_usage is not None and current_usage < max_usage
            ):
                logs_to_process.append(log_event)
                current_usage += 1
            else:
                extra_logs_to_save.append(log_event)
        except Exception as e:
            logger.error(
                f"Error processing langfuse run for project id: {user_data['project_id']}, {e}"
            )

    langfuse.shutdown()

    await change_last_langfuse_extract(
        project_id=user_data["project_id"],
        new_last_extract_date=str(datetime.now()),
    )

    background_tasks.add_task(
        process_log,
        project_id=user_data["project_id"],
        org_id=user_data["org_id"],
        logs_to_process=logs_to_process,
        extra_logs_to_save=extra_logs_to_save,
    )

    logger.debug(
        f"Finished processing langsmith runs for project id: {user_data['project_id']}"
    )

    await encrypt_and_store_langfuse_credentials(
        project_id=user_data["project_id"],
        langfuse_secret_key=user_data["langfuse_credentials"]["langfuse_secret_key"],
        langfuse_public_key=user_data["langfuse_credentials"]["langfuse_public_key"],
    )

    return {"status": "ok"}

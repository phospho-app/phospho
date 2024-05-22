# Models
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
)
from app.services.projects import get_project_by_id
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger

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
        save_task=False,
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
    description="Run a recipe on a task",
)
async def post_run_job_on_task(
    background_tasks: BackgroundTasks,
    request: RunRecipeOnTaskRequest,
    is_request_authenticated: bool = Depends(authenticate_key),
):
    # If there is no tasks to process, return
    if len(request.tasks) == 0:
        logger.debug("No tasks to process.")
        return {"status": "no tasks to process"}

    if request.recipe.recipe_type == "event_detection":
        logger.info(
            f"Running job {request.recipe.recipe_type} on {len(request.tasks)} tasks."
        )
        background_tasks.add_task(
            recipe_pipeline,
            tasks=request.tasks,
            recipe=request.recipe,
        )
        return {"status": "ok", "nb_job_results": len(request.tasks)}

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid job type. Only 'event_detection' is supported.",
        )


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

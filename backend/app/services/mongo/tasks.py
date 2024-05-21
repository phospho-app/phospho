from typing import Dict, List, Literal, Optional, cast
from phospho.utils import filter_nonjsonable_keys

import pydantic
from app.db.models import Eval, EventDefinition, Task, Event
from app.db.mongo import get_mongo_db
from fastapi import HTTPException

from app.utils import generate_uuid

from loguru import logger


async def create_task(
    project_id: str,
    org_id: str,
    input: str,
    task_id: Optional[str] = None,
    output: Optional[str] = None,
    additional_input: Optional[dict] = None,
    data: Optional[dict] = None,
    session_id: Optional[str] = None,
    flag: Optional[str] = None,
) -> Task:
    mongo_db = await get_mongo_db()
    if task_id is None:
        task_id = generate_uuid()
    task_data = Task(
        id=task_id,
        input=input,
        project_id=project_id,
        org_id=org_id,
        session_id=session_id,
        output=output,
        additional_input=additional_input,
        data=data,
        flag=flag,
    )
    # Filter non-jsonable values
    if task_data.metadata is not None:
        task_data.metadata = filter_nonjsonable_keys(task_data.metadata)

    # Create a new task
    doc_creation = await mongo_db["tasks"].insert_one(task_data.model_dump())
    if not doc_creation:
        raise Exception("Failed to insert the task in database")
    return task_data


async def get_task_by_id(task_id: str) -> Task:
    mongo_db = await get_mongo_db()
    task = await mongo_db["tasks"].find_one({"id": task_id})
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Account for schema discrepancies
    if "id" not in task.keys():
        task["id"] = task_id

    if task["flag"] == "undefined":
        task["flag"] = None

    try:
        task = Task.model_validate(task, strict=True)
    except pydantic.ValidationError as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate task: {e}")
    return task


async def flag_task(
    task_model: Task,
    flag: str,
    source: Optional[str] = None,
    notes: Optional[str] = None,
) -> Task:
    mongo_db = await get_mongo_db()

    if source is None:
        source = "user"

    # Create the Evaluation object and store it in the db
    try:
        flag = cast(Literal["success", "failure"], flag)
        eval_data = Eval(
            project_id=task_model.project_id,
            session_id=task_model.session_id,
            task_id=task_model.id,
            value=flag,
            source=source,
            notes=notes,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create eval: {e}")

    eval_insert = await mongo_db["evals"].insert_one(eval_data.model_dump())

    # Update the task object
    try:
        update_payload: Dict[str, object] = {}
        update_payload["flag"] = flag
        if notes is not None:
            update_payload["notes"] = notes
        update_payload["last_eval"] = eval_data.model_dump()
        task_ref = await mongo_db["tasks"].update_one(
            {"id": task_model.id},
            {"$set": update_payload},
        )
        task_model.flag = flag
        task_model.notes = notes
        task_model.last_eval = eval_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update Task {task_model.id}: {e}"
        )

    return task_model


async def update_task(
    task_model: Task,
    metadata: Optional[dict] = None,
    data: Optional[dict] = None,
    notes: Optional[str] = None,
    flag: Optional[str] = None,
    flag_source: Optional[str] = None,
) -> Task:
    mongo_db = await get_mongo_db()

    # Update the task object if the fields are not None
    if metadata is not None:
        # Filter non-jsonable values
        metadata = filter_nonjsonable_keys(metadata)
        task_model.metadata = metadata
    if data is not None:
        task_model.data = data
    if notes is not None:
        task_model.notes = notes
    if flag is not None:
        task_model.flag = flag
        flag_source = flag_source
        if flag_source is None:
            flag_source = "user"
        # Create the Evaluation object and store it in the db
        flag = cast(Literal["success", "failure"], flag)
        eval_data = Eval(
            project_id=task_model.project_id,
            session_id=task_model.session_id,
            task_id=task_model.id,
            value=flag,
            source=flag_source,
        )
        eval_insert = await mongo_db["evals"].insert_one(eval_data.model_dump())
        task_model.last_eval = eval_data

    # Update the task object
    try:
        task_ref = await mongo_db["tasks"].update_one(
            {"id": task_model.id}, {"$set": task_model.model_dump()}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update Task {task_model.id}: {e}"
        )

    return task_model


async def add_event_to_task(
    task: Task, event: EventDefinition, event_source: str = "owner"
) -> Task:
    """
    Adds an event to a task
    """
    mongo_db = await get_mongo_db()
    # Check if the event is already in the task
    if task.events is not None and event.event_name in [
        e.event_name for e in task.events
    ]:
        return task

    # Add the event to the events collection and to the task
    detected_event_data = Event(
        event_name=event.event_name,
        task_id=task.id,
        session_id=task.session_id,
        project_id=task.project_id,
        source=event_source,
        webhook=event.webhook,
        org_id=task.org_id,
        event_definition=event,
    )
    _ = await mongo_db["events"].insert_one(detected_event_data.model_dump())

    if task.events is None:
        task.events = []
    task.events.append(detected_event_data)

    # Update the task object
    _ = await mongo_db["tasks"].update_many(
        {"id": task.id, "project_id": task.project_id}, {"$set": task.model_dump()}
    )

    return task


async def remove_event_from_task(task: Task, event_name: str) -> Task:
    """
    Removes an event from a task
    """
    mongo_db = await get_mongo_db()
    # Check if the event is in the task
    if task.events is not None and event_name in [e.event_name for e in task.events]:
        # Mark the event as removed in the events database
        event_ref = await mongo_db["events"].update_many(
            {"task_id": task.id, "event_name": event_name},
            {"$set": {"removed": True}},
        )
        # Remove the event from the task
        task.events = [e for e in task.events if e.event_name != event_name]

        # Update the task object
        task_ref = await mongo_db["tasks"].update_one(
            {"id": task.id, "project_id": task.project_id}, {"$set": task.model_dump()}
        )

    return task


async def get_total_nb_of_tasks(
    project_id: str,
    flag: Optional[str] = None,
    event_name: Optional[List[str]] = None,
    sentiment: Optional[str] = None,
    last_eval_source: Optional[str] = None,
    metadata: Optional[Dict[str, object]] = None,
    created_at_start: Optional[int] = None,
    created_at_end: Optional[int] = None,
    language: Optional[str] = None,
    **kwargs,
) -> Optional[int]:
    """
    Get the total number of tasks of a project.
    """
    mongo_db = await get_mongo_db()
    # Time range filter
    global_filters: Dict[str, object] = {"project_id": project_id}
    if created_at_start is not None:
        global_filters["created_at"] = {"$gte": created_at_start}
    if created_at_end is not None:
        global_filters["created_at"] = {
            **global_filters.get("created_at", {}),
            "$lte": created_at_end,
        }
    if last_eval_source is not None:
        if last_eval_source.startswith("phospho"):
            # We want to filter on the source starting with "phospho"
            global_filters["evaluation_source"] = {"$regex": "^phospho"}
        else:
            # We want to filter on the source not starting with "phospho"
            global_filters["evalutation_source"] = {"$regex": "^(?!phospho).*"}
    if metadata is not None:
        for key, value in metadata.items():
            global_filters[f"metadata.{key}"] = value
    if language is not None:
        global_filters["language"] = language
    if sentiment is not None:
        global_filters["sentiment.label"] = sentiment
    if flag is not None:
        global_filters["flag"] = flag

    logger.debug(event_name)
    if event_name is not None:
        global_filters["$and"] = [
            {"events": {"$ne": []}},
            {"events": {"$elemMatch": {"event_name": {"$in": event_name}}}},
        ]
        query_result = (
            await mongo_db["tasks"]
            .aggregate(
                [
                    {"$match": global_filters},
                    {"$count": "nb_tasks"},
                ]
            )
            .to_list(length=1)
        )
        if query_result is not None and len(query_result) > 0:
            total_nb_tasks = query_result[0]["nb_tasks"]
        else:
            total_nb_tasks = None

    else:
        total_nb_tasks = await mongo_db["tasks"].count_documents(global_filters)

    logger.debug(f"Total number of tasks: {total_nb_tasks}")
    return total_nb_tasks

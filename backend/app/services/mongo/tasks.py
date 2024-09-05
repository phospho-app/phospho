import datetime
from typing import Dict, List, Literal, Optional, Tuple, cast
from app.api.platform.models.explore import Pagination, Sorting
from phospho.models import ProjectDataFilters, ScoreRange, HumanEval
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
    task = await mongo_db["tasks_with_events"].find_one({"id": task_id})
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


async def human_eval_task(
    task_model: Task,
    human_eval: str,
    source: Optional[str] = None,
    notes: Optional[str] = None,
) -> Task:
    """
    Adds a human evaluation to a task and updates evaluation data for retrocompatibility
    """

    mongo_db = await get_mongo_db()

    if source is None:
        source = "owner"

    # Create the Evaluation object and store it in the db
    try:
        flag = cast(Literal["success", "failure"], human_eval)
        eval_data = Eval(
            project_id=task_model.project_id,
            session_id=task_model.session_id,
            task_id=task_model.id,
            value=flag,
            source=source,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create eval: {e}")

    await mongo_db["evals"].insert_one(eval_data.model_dump())

    # Update the task object
    try:
        update_payload: Dict[str, object] = {}
        update_payload["flag"] = flag
        update_payload["last_eval"] = eval_data.model_dump()
        update_payload["human_eval"] = HumanEval(flag=human_eval).model_dump()
        update_payload["notes"] = notes
        await mongo_db["tasks"].update_one(
            {"id": task_model.id},
            {"$set": update_payload},
        )
        task_model.flag = flag
        task_model.last_eval = eval_data
        task_model.human_eval = HumanEval(flag=human_eval)
        task_model.notes = notes
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update Task {task_model.id}: {e}"
        )
    # Update the session object

    try:
        tasks = (
            await mongo_db["tasks"]
            .find({"session_id": task_model.session_id})
            .to_list(length=None)
        )
        nbr_success = 0
        nbr_failure = 0
        for task in tasks:
            logger.debug(f"Task {task}")
            validated_task = Task.model_validate(task)
            if (
                validated_task.human_eval is None
                or validated_task.human_eval.flag is None
            ):
                continue
            elif validated_task.human_eval.flag == "success":
                nbr_success += 1
            elif validated_task.human_eval.flag == "failure":
                nbr_failure += 1
        if nbr_success + nbr_failure == 0:
            session_flag = None
        elif nbr_success >= nbr_failure:
            session_flag = "success"
        else:
            session_flag = "failure"
        await mongo_db["sessions"].update_one(
            {"id": validated_task.session_id},
            {"$set": {"stats.human_eval": session_flag}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update Session {task_model.session_id}: {e}",
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
        await mongo_db["evals"].insert_one(eval_data.model_dump())
        task_model.last_eval = eval_data

    # Update the task object
    try:
        await mongo_db["tasks"].update_one(
            {"id": task_model.id}, {"$set": task_model.model_dump()}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update Task {task_model.id}: {e}"
        )

    return task_model


async def add_event_to_task(
    task: Task,
    event: EventDefinition,
    event_source: str = "owner",
    score_range_value: Optional[float] = None,
    score_category_label: Optional[str] = None,
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

    if (
        score_range_value is None
        and score_category_label is not None
        and event.score_range_settings.score_type == "category"
        and event.score_range_settings.categories is not None
    ):
        score_range_value = (
            event.score_range_settings.categories.index(score_category_label) + 1
        )
    if score_range_value is None:
        score_range = None
    else:
        score_range = ScoreRange(
            score_type=event.score_range_settings.score_type,
            min=event.score_range_settings.min,
            max=event.score_range_settings.max,
            label=score_category_label,
            value=score_range_value,
        )

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
        confirmed=True,
        score_range=score_range,
    )
    await mongo_db["events"].insert_one(detected_event_data.model_dump())

    if task.events is None:
        task.events = []
    task.events.append(detected_event_data)

    return task


async def remove_event_from_task(task: Task, event_name: str) -> Task:
    """
    Removes an event from a task
    """
    mongo_db = await get_mongo_db()
    # Check if the event is in the task
    if task.events is not None and event_name in [e.event_name for e in task.events]:
        # Mark the event as removed in the events database
        await mongo_db["events"].update_many(
            {"task_id": task.id, "event_name": event_name},
            {
                "$set": {
                    "removed": True,
                    "removal_reason": "removed_by_user_from_session",
                }
            },
        )
        # Remove the event from the task
        task.events = [e for e in task.events if e.event_name != event_name]

    return task


async def task_filtering_pipeline_match(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
    prefix: str = "",
    collection: str = "tasks",
) -> Tuple[Dict[str, object], str]:
    """
    Generate the match part of the aggregation pipeline for task filtering.

    Args:
        project_id: The project ID.
        filters: The filters to apply.
        prefix: The prefix to use for the fields in the match query.
    """

    if filters is None:
        filters = ProjectDataFilters()

    if prefix != "" and not prefix.endswith("."):
        # Add a dot at the end of the prefix if it is not already there
        prefix += "."

    match: Dict[str, object] = {f"{prefix}project_id": project_id}

    if filters.tasks_ids is not None:
        match[f"{prefix}id"] = {"$in": filters.tasks_ids}

    # Cast the created_at filters to int
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    if filters.created_at_start is not None:
        match[f"{prefix}created_at"] = {"$gte": filters.created_at_start}
    if filters.created_at_end is not None:
        match[f"{prefix}created_at"] = {
            **match.get(f"{prefix}created_at", {}),
            "$lte": filters.created_at_end,
        }

    if filters.last_eval_source is not None:
        if filters.last_eval_source.startswith("phospho"):
            # We want to filter on the source starting with "phospho"
            match[f"{prefix}last_eval.source"] = {"$regex": "^phospho"}
        else:
            # We want to filter on the source not starting with "phospho"
            match[f"{prefix}last_eval.source"] = {"$regex": "^(?!phospho).*"}

    if filters.metadata is not None:
        for key, value in filters.metadata.items():
            match[f"{prefix}metadata.{key}"] = value

    if filters.language is not None:
        match[f"{prefix}language"] = filters.language

    if filters.sentiment is not None:
        match[f"{prefix}sentiment.label"] = filters.sentiment

    if filters.flag is not None:
        match[f"{prefix}flag"] = filters.flag

    if filters.event_name is not None:
        collection = "tasks_with_events"
        match["$and"] = [
            {f"{prefix}events": {"$ne": []}},
            {
                f"{prefix}events": {
                    "$elemMatch": {"event_name": {"$in": filters.event_name}}
                }
            },
        ]

    if filters.event_id is not None:
        collection = "tasks_with_events"
        match["$and"] = [
            {f"{prefix}events": {"$ne": []}},
            {f"{prefix}events": {"$elemMatch": {"id": {"$in": filters.event_id}}}},
        ]

    if filters.clustering_id is not None and filters.clusters_ids is None:
        # Fetch the clusterings
        mongo_db = await get_mongo_db()
        clustering = await mongo_db["private-clusterings"].find_one(
            {"id": filters.clustering_id}
        )
        if clustering:
            filters.clusters_ids = []
            filters.clusters_ids.extend(clustering.get("clusters_ids", []))

    if filters.clusters_ids is not None:
        # Fetch the cluster
        mongo_db = await get_mongo_db()
        clusters = (
            await mongo_db["private-clusters"]
            .find({"id": {"$in": filters.clusters_ids}})
            .to_list(length=None)
        )
        if clusters:
            new_task_ids = []
            for cluster in clusters:
                new_task_ids.extend(cluster.get("tasks_ids", []))
            current_task_ids = match.get(f"{prefix}id", {"$in": []})["$in"]
            if current_task_ids:
                # Do the intersection of the current task ids and the new task ids
                new_task_ids = list(set(current_task_ids).intersection(new_task_ids))
            match[f"{prefix}id"] = {"$in": new_task_ids}

    if filters.has_notes is not None and filters.has_notes:
        match["$and"] = [
            {f"{prefix}notes": {"$exists": True}},
            {f"{prefix}notes": {"$ne": None}},
            {f"{prefix}notes": {"$ne": ""}},
        ]

    if filters.is_last_task is not None:
        logger.debug("FILTER: is last task")
        from app.services.mongo.sessions import compute_task_position
        from copy import copy

        filters_without_latest = copy(filters)
        filters_without_latest.is_last_task = None

        logger.debug("Computing task position...")
        await compute_task_position(
            project_id=project_id, filters=filters_without_latest
        )
        match[f"{prefix}is_last_task"] = filters.is_last_task

    if filters.sessions_ids is not None:
        match[f"{prefix}session_id"] = {"$in": filters.sessions_ids}

    return match, collection


async def get_total_nb_of_tasks(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
) -> Optional[int]:
    """
    Get the total number of tasks of a project.
    """
    mongo_db = await get_mongo_db()
    global_filters, collection = await task_filtering_pipeline_match(
        project_id=project_id, filters=filters
    )

    query_result = (
        await mongo_db[collection]
        .aggregate(
            [
                {"$match": global_filters},
                {"$count": "nb_tasks"},
            ]
        )
        .to_list(length=1)
    )

    logger.info(f"Query result: {query_result}")
    if len(query_result) == 0:
        return None

    total_nb_tasks = query_result[0]["nb_tasks"]
    return total_nb_tasks


async def label_sentiment_analysis(
    project_id: str,
    score_threshold: Optional[float] = None,
    magnitude_threshold: Optional[float] = None,
) -> None:
    """
    Label sentiment analysis for a project.
    """
    mongo_db = await get_mongo_db()

    if score_threshold is None:
        score_threshold = 0.5
    if magnitude_threshold is None:
        magnitude_threshold = 0.3

    _ = await mongo_db["tasks"].update_many(
        # This query matches all tasks beloging to the project_id and with a score higher than score_threshold
        {
            "project_id": project_id,
            "sentiment.score": {"$gt": score_threshold},
        },
        {
            "$set": {"sentiment.label": "positive"},
        },
    )
    _ = await mongo_db["tasks"].update_many(
        # This query matches all tasks beloging to the project_id and with a score lower than -score_threshold
        {
            "project_id": project_id,
            "sentiment.score": {"$lt": -score_threshold},
        },
        {
            "$set": {"sentiment.label": "negative"},
        },
    )
    _ = await mongo_db["tasks"].update_many(
        # This query matches all tasks beloging to the project_id and with a score between -score_threshold and score_threshold
        # It also filters out tasks with a magnitude higher than magnitude_threshold
        {
            "project_id": project_id,
            "sentiment.score": {"$gte": -score_threshold, "$lte": score_threshold},
            "sentiment.magnitude": {"$lt": magnitude_threshold},
        },
        {
            "$set": {"sentiment.label": "neutral"},
        },
    )
    _ = await mongo_db["tasks"].update_many(
        # This query matches all tasks beloging to the project_id and with a score between -score_threshold and score_threshold
        # It also filters out tasks with a magnitude higher than magnitude_threshold
        {
            "project_id": project_id,
            "sentiment.score": {"$gte": -score_threshold, "$lte": score_threshold},
            "sentiment.magnitude": {"$gte": magnitude_threshold},
        },
        {
            "$set": {"sentiment.label": "mixed"},
        },
    )

    return None


async def get_all_tasks(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
    get_events: bool = True,
    get_tests: bool = False,
    validate_metadata: bool = False,
    limit: Optional[int] = None,
    pagination: Optional[Pagination] = None,
    sorting: Optional[List[Sorting]] = None,
) -> List[Task]:
    """
    Get all the tasks of a project.
    """

    mongo_db = await get_mongo_db()
    collection = "tasks"

    main_filter, collection = await task_filtering_pipeline_match(
        filters=filters, project_id=project_id, collection=collection
    )

    logger.info(f"Get all tasks with filters: {main_filter}")

    if not get_tests:
        main_filter["test_id"] = None

    pipeline: List[Dict[str, object]] = [
        {"$match": main_filter},
    ]

    # Get rid of the raw_input and raw_output fields
    pipeline.append(
        {
            "$project": {
                "additional_input": 0,
                "additional_output": 0,
            }
        }
    )

    if not get_events:
        collection = "tasks"

    # To avoid the sort to OOM on Serverless MongoDB executor, we restrain the pipeline to the necessary fields...
    if sorting is None:
        sorting_dict = {"created_at": -1}
    else:
        sorting_dict = {sort.id: 1 if sort.desc else -1 for sort in sorting}
    pipeline.extend(
        [
            {
                "$project": {
                    "id": 1,
                    **{sort_key: 1 for sort_key in sorting_dict.keys()},
                }
            },
            {"$sort": sorting_dict},
        ]
    )

    # Add pagination
    if pagination:
        pipeline.extend(
            [
                {"$skip": pagination.page * pagination.per_page},
                {"$limit": pagination.per_page},
            ]
        )
        limit = None

    # ... and then we add the lookup and the deduplication
    pipeline.extend(
        [
            {
                "$lookup": {
                    "from": "tasks_with_events",
                    "localField": "id",
                    "foreignField": "id",
                    "as": "tasks",
                }
            },
            # unwind the tasks array
            {"$unwind": "$tasks"},
            # Replace the root with the tasks
            {"$replaceRoot": {"newRoot": "$tasks"}},
        ]
    )

    tasks = await mongo_db[collection].aggregate(pipeline).to_list(length=limit)

    # Cast to tasks
    valid_tasks = [Task.model_validate(data) for data in tasks]

    if validate_metadata:
        for task in valid_tasks:
            # Remove the _id field from the task metadata
            if task.metadata is not None:
                task.metadata = filter_nonjsonable_keys(task.metadata)

    return valid_tasks

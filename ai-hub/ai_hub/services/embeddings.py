from ai_hub.models.progress_bar import ProgressBar
from ai_hub.models.users import User
from ai_hub.services.formatting import format_user_messages
from ai_hub.services.summaries import (
    generate_intent_summary_phospho_job,
)
from loguru import logger
from openai import AsyncOpenAI
from typing import Dict, List, Literal, Optional, Tuple, Union, cast
from openai.types import Embedding as OpenAIEmbedding
from pydantic import ValidationError

from phospho import lab
from phospho.models import Task, Session

from ai_hub.core import config
from ai_hub.models.embeddings import Embedding, EmbeddingRequest
from ai_hub.db.mongo import get_mongo_db
from ai_hub.models.clusterings import Clustering


openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


def get_llm_and_provider_from_model(
    model: Literal["intent-embed", "intent-embed-2", "intent-embed-3"],
) -> Tuple[
    str,
    Literal[
        "openai",
        "mistral",
        "ollama",
        "solar",
        "together",
        "anyscale",
        "fireworks",
        "azure",
    ],
]:
    if model == "intent-embed":
        return "gpt-3.5-turbo", "openai"
    elif model == "intent-embed-2":
        return "meta-llama/Meta-Llama-3-8B-Instruct", "anyscale"
    elif model == "intent-embed-3":
        return "gpt-4o-mini", "openai"
    else:
        raise ValueError(f"Invalid model: {model}")


async def generate_embeddings(embedding_request: EmbeddingRequest) -> Embedding:
    """
    Generate the embeddings for a given text and model
    """
    logger.debug(f"Generating embeddings for text: {embedding_request.text}")

    model_llm, provider = get_llm_and_provider_from_model(embedding_request.model)
    # Generate an intent summary of for each message
    job_result = await generate_intent_summary_phospho_job(
        lab.Message(
            content=embedding_request.text,
        ),
        model_llm=model_llm,
        provider=provider,
        instruction=embedding_request.instruction,
        scope=None,
    )
    intent_summary = job_result.value

    assert intent_summary is not None, "Intent summary is None in generate_embeddings"

    # Embed the intent summary using openai
    embdeding_results_response = await openai_client.embeddings.create(
        model=config.OPENAI_EMBEDDINGS_MODEL,
        input=intent_summary,
        encoding_format="float",
    )
    # Store the embeddings
    embeddings_vector = embdeding_results_response.data[0].embedding

    embedding = Embedding(
        text=embedding_request.text,
        embeddings=embeddings_vector,
        model=embedding_request.model,
        org_id=embedding_request.org_id,
        project_id=embedding_request.project_id,
        task_id=embedding_request.task_id,
        instruction=embedding_request.instruction,
    )

    return embedding


async def generate_datas_embeddings(
    datas: List[Union[Task, Session, User]],
    clustering: Clustering,
    len_datas: int,
    progress_bar: ProgressBar,
    emb_model: Literal[
        "intent-embed", "intent-embed-2", "intent-embed-3"
    ] = "intent-embed-3",
    batch_size: int = 1024,
    get_previous_tasks: bool = True,
    scope: Literal["messages", "sessions", "users"] = "messages",
    instruction: Optional[str] = "user intent",
) -> List[Embedding]:
    """
    Generate embeddings for a batch of tasks dicts
    2048 is the maximum parallelism allowed by the openai embeddings API
    In case the number of texts is greater than the max_parallelism, the texts are cropped
    """
    # Log an error if the number of texts is greater than the max_parallelism and crop the texts

    model_llm, provider = get_llm_and_provider_from_model(emb_model)
    mongo_db = await get_mongo_db()
    if scope == "messages":
        previous_tasks: Dict[str, List[Task]] = {}  # {session_id: [task, task, ...]}
        if not all(isinstance(data, Task) for data in datas):
            raise ValueError(
                f"When using scope {scope}, datas should be a list of Task"
            )
        tasks_datas = cast(List[Task], datas)
        if get_previous_tasks:
            # Fetch the previous tasks
            # I want to make sure datas is only a list of Task

            previous_tasks_in_db = (
                await mongo_db["tasks"]
                .aggregate(
                    [
                        {
                            "$match": {
                                "project_id": datas[0].project_id,
                                "session_id": {
                                    "$in": [task.session_id for task in tasks_datas]
                                },
                                # "created_at": {"$lt": task.created_at},
                            }
                        },
                        # Group by the session_id and get all the tasks
                        {
                            "$group": {
                                "_id": "$session_id",
                                "tasks": {"$push": "$$ROOT"},
                            }
                        },
                    ],
                    allowDiskUse=True,
                )
                .to_list(length=None)
            )
            previous_tasks = {
                pt["_id"]: [Task.model_validate(t) for t in pt["tasks"]]
                for pt in previous_tasks_in_db
            }

        messages = []
        for task in tasks_datas:
            if task.session_id is not None:
                valid_previous_tasks: List[Task] = previous_tasks.get(
                    task.session_id, []
                )
                # Keep only those tasks that are before the current task
                valid_previous_tasks = [
                    t for t in valid_previous_tasks if t.created_at < task.created_at
                ]
                message = lab.Message.from_task(
                    task,
                    previous_tasks=valid_previous_tasks,
                    ignore_last_output=False,
                    metadata={
                        "task_id": task.id,
                        # We don't keep session_id, so as not to confuse this with session-scoped embeddings
                        "session_id": None,
                    },
                )
                messages.append(message)
    elif scope == "sessions":
        messages = []
        if not all(isinstance(data, Session) for data in datas):
            raise ValueError(
                f"When using scope {scope}, datas should be a list of Session"
            )
        sessions_datas = cast(List[Session], datas)
        for session in sessions_datas:
            try:
                message = lab.Message.from_session(
                    session,
                    metadata={
                        "session_id": session.id,
                        # We don't keep any reference to the tasks of the sessions, to avoid confusion
                        "task_id": None,
                    },
                )
                messages.append(message)
            except ValueError:
                logger.warning(f"Session {session.id} is empty. Skipping")
                continue
            except Exception as e:
                logger.error(f"Error while generating messages: {e}")
                continue
    elif scope == "users":
        if not all(isinstance(data, User) for data in datas):
            raise ValueError(
                f"When using scope {scope}, datas should be a list of User"
            )
        users_datas = cast(List[User], datas)
        messages = await format_user_messages(
            datas=users_datas,
            model_llm=model_llm,
            provider=provider,
            instruction=instruction,
        )

    async def generate_intent_summary_phospho_job_with_progress(
        message: lab.Message,
        model_llm: str,
        provider: Literal[
            "openai",
            "mistral",
            "ollama",
            "solar",
            "together",
            "anyscale",
            "fireworks",
            "azure",
        ],
        instruction: str,
        scope: Literal["messages", "sessions", "users"] | None,
    ) -> lab.JobResult:
        """
        This function is used to carry on the progress bar update
        """
        return await generate_intent_summary_phospho_job(
            message=message,
            model_llm=model_llm,
            provider=provider,
            instruction=instruction,
            scope=scope,
            progress_bar=progress_bar,
        )

    # Generate an intent summary for each text
    workload = lab.Workload(
        jobs=[
            lab.Job(
                id="intent_summary",
                job_function=generate_intent_summary_phospho_job_with_progress,
                config=lab.JobConfig(
                    model_llm=model_llm,
                    provider=provider,
                    instruction=instruction,
                    scope=scope,
                ),
            ),
        ]
    )
    await workload.async_run(messages, max_parallelism=100)

    # We create two lists of same sizes and order:
    # - texts_to_embed: the texts to embed that we'll pass to OpenAI
    # - data_ids_of_texts_to_embed: the data ids of the texts to embed. We'll use them to create the Embedding objects
    # The dict data_ids_to_metadata will store the metadata of the texts to embed. We'll use it to create the Embedding objects
    texts_to_embed: List[str] = []
    texts_to_embed_data_id: List[str] = []
    data_ids_to_summary: Dict[str, str] = {}

    if workload.results is None:
        return []
    for message_id, job_results in workload.results.items():
        if job_results["intent_summary"].result_type == lab.ResultType.error:
            logger.warning(
                f"Error while generating intent summary for message {message_id}. Skipping: {job_results['intent_summary'].logs}"
            )
        else:
            texts_to_embed.append(job_results["intent_summary"].value)
            if job_results["intent_summary"].metadata.get("task_id") is not None:
                task_id = job_results["intent_summary"].metadata["task_id"]
            else:
                task_id = None
            if job_results["intent_summary"].metadata.get("session_id") is not None:
                session_id = job_results["intent_summary"].metadata["session_id"]
            else:
                session_id = None
            if job_results["intent_summary"].metadata.get("user_id") is not None:
                user_id = job_results["intent_summary"].metadata["user_id"]
            # Note: We use elif so that an embedding has a single reference to task_id or session_id
            if task_id is not None:
                texts_to_embed_data_id.append(task_id)
                data_ids_to_summary[task_id] = job_results["intent_summary"].value
            elif session_id is not None:
                texts_to_embed_data_id.append(session_id)
                data_ids_to_summary[session_id] = job_results["intent_summary"].value
            elif user_id is not None:
                texts_to_embed_data_id.append(user_id)
                data_ids_to_summary[user_id] = job_results["intent_summary"].value

    if len(texts_to_embed) == 0:
        return []

    # TODO: save the LLM call for later use
    # Batch the texts to embed
    embedding_results_response: List[OpenAIEmbedding] = []
    if clustering.percent_of_completion is None:
        # This is the last step of the clustering
        clustering.percent_of_completion = 50
    for i in range(1 + len(texts_to_embed) // batch_size):
        batch_texts_to_embed = texts_to_embed[
            i * batch_size : min((i + 1) * batch_size, len(texts_to_embed))
        ]
        # Call openai embeddings API
        batch_embedding_results_response = await openai_client.embeddings.create(
            model=config.OPENAI_EMBEDDINGS_MODEL,
            input=batch_texts_to_embed,
            encoding_format="float",
        )
        embedding_results_response.extend(batch_embedding_results_response.data)

        # Update the percentage of completion in clustering
        nb_texts_embedded = min((i + 1) * batch_size, len(texts_to_embed))
        clustering.percent_of_completion += 50 * nb_texts_embedded / len_datas
        await mongo_db[config.CLUSTERINGS_COLLECTION].update_one(
            {"id": clustering.id},
            {"$set": {"percent_of_completion": clustering.percent_of_completion}},
        )

    embeddings = []
    datas_ids_to_datas = {data.id: data for data in datas}

    for data_id, openai_embedding in zip(
        texts_to_embed_data_id, embedding_results_response
    ):
        data: Union[Task, Session, User, None] = datas_ids_to_datas.get(data_id)
        if data is None:
            logger.warning(
                f"Data with id {data_id} not found in the data list. Skipping"
            )
            continue
        text = data_ids_to_summary.get(data_id)

        if text is None:
            text = "No summary available"

        embedding = Embedding(
            text=text,
            embeddings=openai_embedding.embedding,
            model=emb_model,
            org_id=data.org_id,
            project_id=data.project_id,
            scope=scope,
            # We use either task_id or session_id, not both
            task_id=data.id if isinstance(data, Task) else None,
            session_id=data.id if isinstance(data, Session) else None,
            user_id=data.id if isinstance(data, User) else None,
            instruction=instruction,
        )
        embeddings.append(embedding)

    return embeddings


async def save_embedding(embedding: Embedding) -> None:
    # save to DB
    mongo_db = await get_mongo_db()

    # TODO: Validate the embedding pydantic model

    await mongo_db[config.EMBEDDINGS_COLLECTION].insert_one(embedding.model_dump())

    logger.debug("Embedding saved")

    # USe an LLM to generate a summary of the clusters for each


async def get_project_embeddings(
    project_id: str,
    progress_bar: ProgressBar,
    datas: Union[List[Task], List[Session], List[User], None] = None,
    batch_size: int = 1024,
    model: Literal[
        "intent-embed", "intent-embed-2", "intent-embed-3"
    ] = "intent-embed-3",
    instruction: Optional[str] = "user intent",
) -> List[Embedding]:
    """
    Fetch the existing embeddings for a project.

    Use batching to fetch the embeddings in chunks of batch_size.
    """
    mongo_db = await get_mongo_db()
    valid_embeddings = []
    if datas is None:
        datas = []
    tasks_ids = [data.id for data in datas if isinstance(data, Task)]
    sessions_ids = [data.id for data in datas if isinstance(data, Session)]
    users_ids = [data.id for data in datas if isinstance(data, User)]

    main_filter = {
        "project_id": project_id,
        "model": model,
        "instruction": instruction,
        "$or": [
            {"task_id": {"$in": tasks_ids}},
            {"session_id": {"$in": sessions_ids}},
            {"user_id": {"$in": users_ids}},
        ],
    }

    number_embeddings_in_db = await mongo_db[
        config.EMBEDDINGS_COLLECTION
    ].count_documents(main_filter)

    logger.debug(f"Number of embeddings in DB: {number_embeddings_in_db}")
    for i in range(1 + number_embeddings_in_db // batch_size):
        embeddings = (
            await mongo_db[config.EMBEDDINGS_COLLECTION]
            .aggregate(
                [
                    {"$match": main_filter},
                    {
                        "$project": {
                            "id": 1,
                            "created_at": 1,
                            "task_id": 1,
                            "session_id": 1,
                            "user_id": 1,
                        }
                    },
                    {"$sort": {"created_at": -1}},
                    # deduplicate based on task_id if task_id not None or session_id
                    {
                        "$group": {
                            "_id": {
                                "task_id": "$task_id",
                                "session_id": "$session_id",
                                "user_id": "$user_id",
                            },
                            "id": {"$first": "$id"},
                        }
                    },
                    {"$skip": i * batch_size},
                    {"$limit": batch_size},
                    # lookup the embeddings
                    {
                        "$lookup": {
                            "from": config.EMBEDDINGS_COLLECTION,
                            "localField": "id",
                            "foreignField": "id",
                            "as": "embeddings",
                        }
                    },
                    {"$unwind": "$embeddings"},
                    {"$replaceRoot": {"newRoot": "$embeddings"}},
                ]
            )
            .to_list(length=batch_size)
        )
        if embeddings is None:
            continue
        logger.debug(f"Embeddings: {len(embeddings)}")
        for emb in embeddings:
            try:
                valid_embeddings.append(Embedding.model_validate(emb))
            except ValidationError:
                # logger.warning(f"Skipping invalid embedding document: {e}")
                continue
        logger.debug(f"Valid embeddings: {len(valid_embeddings)}")
        await progress_bar.update(new_embeddings_processed=len(embeddings))

    return valid_embeddings

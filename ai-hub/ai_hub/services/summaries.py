from typing import Dict, Literal, Optional, Union
import random

from ai_hub.models.clusterings import Cluster
from ai_hub.models.embeddings import Embedding
from ai_hub.models.progress_bar import ProgressBar
from ai_hub.models.users import User
from loguru import logger
from openai import AsyncOpenAI
from phospho import lab
from phospho.utils import shorten_text
from ai_hub.core import config


from phospho.models import Session, Task

openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


async def generate_intent_summary_phospho_job(
    message: lab.Message,
    progress_bar: Optional[ProgressBar] = None,
    model_llm: str = "gpt-4o-mini",
    provider: Literal[
        "openai",
        "mistral",
        "ollama",
        "solar",
        "together",
        "anyscale",
        "fireworks",
        "azure",
    ] = "openai",
    instruction: Optional[str] = "user intent",
    scope: Optional[Literal["messages", "sessions", "users"]] = "messages",
) -> lab.JobResult:
    system_prompt = (
        f"You are a helpful assistant that summarize {instruction} in a sentence."
    )

    if scope == "messages":
        if len(message.previous_messages) > 1:
            prompt = f"""Summarize the LAST interaction of this transcript in a sentence. Focus on {instruction}.\n
<transcript>
{message.transcript(with_previous_messages=True, only_previous_messages=False, max_previous_messages=3, message_content_max_len=4096)}
</transcript>

Summary of {instruction} in a sentence:"""
        else:  # Only one interaction
            prompt = f"""Summarize the interaction in a sentence. Focus on {instruction}.\n
<transcript>
{message.transcript(with_previous_messages=True, only_previous_messages=False, max_previous_messages=3, message_content_max_len=4096)}
</transcript>

Summary of {instruction} in a sentence:"""

    elif scope == "sessions":
        prompt = f"""Summarize this session in a sentence. Focus on {instruction}.\n
<transcript>
{message.transcript(with_previous_messages=True, only_previous_messages=False, message_content_max_len=2048)}
</transcript>

Summary of {instruction} in a sentence:"""

    elif scope == "users":
        # In scope users, the user sessions were summarized by format_user_messages function
        # (Hierarchical summarization)
        # So the message.content already contains the summary of the user sessions
        prompt = f"""Summarize the summaries of interactions of this user in a sentence. Focus on {instruction}.\n
<interactions summaries>
{message.content}
</interactions summaries>

Summary of {instruction} in a sentence:"""
    elif scope is None:
        # For free text summarization
        prompt = f"""Summarize the text in a sentence. Focus on {instruction}.\n
<text>
{shorten_text(message.content, max_length=100_000, margin=20, how="center")}
</text>

Summary of {instruction} in a sentence:"""
    else:
        raise ValueError(f"Invalid scope: {scope}")

    if len(prompt) > 12000:
        logger.warning(
            f"Prompt is too long for message {message.id}. Shortening the prompt"
        )
        prompt = shorten_text(prompt, max_length=12000, margin=20, how="center")

    openai_client = lab.get_async_client(provider)
    try:
        response = await openai_client.chat.completions.create(
            model=model_llm,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
        )
        summary = response.choices[0].message.content

    except Exception as e:
        logger.error(f"Error while generating {instruction} summary: {e}")
        summary = None

    if progress_bar is not None:
        await progress_bar.update()

    if summary is None:
        return lab.JobResult(
            value=None,
            result_type=lab.ResultType.error,
            logs=[
                f"Error while generating {instruction} summary for message {message.id}"
            ],
        )

    return lab.JobResult(
        value=summary,
        result_type=lab.ResultType.string,
        metadata=message.metadata,
    )


async def generate_cluster_description_title(
    cluster: Cluster,
    embeddings: Dict[str, Embedding],
    datas: Dict[str, Union[Task, Session, User]],
    progress_bar: ProgressBar,
    output_format: Literal[
        "title_description", "user_persona", "question_and_answer"
    ] = "title_description",
    openai_model_id: str = "gpt-4o",
    max_samples: int = 15,
    instruction: Optional[str] = "user intent",
) -> Cluster:
    texts_lists = []
    if cluster.embeddings_ids is not None:
        for embedding_id in cluster.embeddings_ids:
            texts_lists.append(embeddings[embedding_id].text)
    data_in_cluster = []
    if cluster.tasks_ids is not None:
        for task_id in cluster.tasks_ids:
            data_in_cluster.append(datas[task_id])
    elif cluster.sessions_ids is not None:
        for session_id in cluster.sessions_ids:
            data_in_cluster.append(datas[session_id])
    elif cluster.users_ids is not None:
        for user_id in cluster.users_ids:
            data_in_cluster.append(datas[user_id])
    # Limit the number of messages to max_samples
    if len(texts_lists) > max_samples:
        texts_lists = random.sample(texts_lists, max_samples)
    if len(data_in_cluster) > max_samples:
        data_in_cluster = random.sample(data_in_cluster, max_samples)  # type: ignore

    prompt_description = ""
    messages_transcripts = ""
    if output_format == "title_description" or output_format == "user_persona":
        prompt_description = "Here is a list of summaries of messages:\n\n"
        for text in texts_lists:
            messages_transcripts += f"- {text}\n"
    else:
        prompt_description = "Here is a list of messages:\n\n"
        for i, data_point in enumerate(data_in_cluster):
            if isinstance(data_point, Task):
                message = lab.models.Message.from_task(data_point)
                messages_transcripts += f"<interaction {i}>\nUser: {message.transcript()}\n</interaction {i}>\n"
            elif isinstance(data_point, Session):
                message = lab.models.Message.from_session(data_point)
                messages_transcripts += (
                    f"<session {i}>\nUser: {message.transcript()}\n</session {i}>\n"
                )
            elif isinstance(data_point, User):
                # Get the summary instead
                messages_transcripts += f"<user {i}>\n{texts_lists[i]}\n</user {i}>\n"
            else:
                raise ValueError(f"Data point type {data_point} not supported")

    prompt_description += messages_transcripts

    if output_format == "title_description":
        system_prompt = (
            f"You are a helpful assistant that summarize {instruction} in a sentence."
        )
        prompt_description += f"\n\nSummarize the list of messages in one or two sentences. Focus on the {instruction}.\n\nSummary:"
    elif output_format == "user_persona":
        system_prompt = f"You are a sharp, concise marketing expert that describes users while focusing on {instruction}."
        prompt_description += (
            "\n\nBased on these messages, generate two sentences describing a user persona.\nFirst sentence: You give age, occupation, country."
            + "\nSecond sentence: List at most 3 behaviors.\nOnly relate information that is in the messages. Only say highly probable information. "
            + f"Focus on '{instruction}'.\n\nTwo sentences describing the user persona:"
        )
    elif output_format == "question_and_answer":
        system_prompt = f"You are a masterful customer support assistant that writes FAQ expertly. You especially know to focus on {instruction}."
        prompt_description += (
            "\n\nBased on these messages, summarize in one or two sentences the assistant's answer to the user inquiries. "
            + "Be synthetic and generic, this answer should address 80% of the people concerns. Do not refer to 'the assistant'. Speak directly to the user."
            + "Do not make up information, only use answers that are in the messages."
            + f"Focus on the {instruction}.\n\nAnswer:"
        )
    else:
        raise ValueError(f"Output format {output_format} not supported")

    response = await openai_client.chat.completions.create(
        model=openai_model_id,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": prompt_description},
        ],
    )

    llm_response = response.choices[0].message.content
    if llm_response:
        # Strip any " or ' characters at the start or end of the sequence
        description: str = llm_response.strip("\"'")
    else:
        description = "No description available"

    if output_format == "title_description":
        # remove "Summary:" at the start
        description = description.replace("Summary:", "")
    if output_format == "question_and_answer":
        # Remove "Sentence 1:" and "Sentence 2:"
        description = description.replace("Sentence 1:", "").replace("Sentence 2:", "")
    description = description.strip()

    if output_format == "title_description":
        system_prompt = "You are a helpful assistant that generates category titles."
        prompt_title = f"Here is a summary of a list of messages:\n\n{description}\n\nGenerate a few words title for this messages category. Focus on the {instruction}\n\nTitle:"
    elif output_format == "user_persona":
        system_prompt = "You are an efficient, concise, sharp marketing expert."
        prompt_title = f"Here is a description of a user:\n\n{description}\n\nDescribe this user in a few words (max 8 words). Focus on the {instruction}\nUser:"
    elif output_format == "question_and_answer":
        system_prompt = f"You are a masterful customer support assistant that writes FAQ expertly. You especially know to focus on {instruction}."
        prompt_title = (
            f"Here are some messages:\n\n{messages_transcripts}"
            f"Here is the answer in the FAQ:\n\n{description}\n\nGenerate a simple, catchy, and generic question corresponding to these messages and this answer. The question should be a few words long, in basic English, and be understood by 80% of the population. "
            + f"Focus on the {instruction}\n\nQuestion:"
        )

    response = await openai_client.chat.completions.create(
        model=openai_model_id,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": prompt_title},
        ],
    )
    llm_response = response.choices[0].message.content

    if llm_response:
        title: str = llm_response.strip("\"'")
    else:
        title = "No title"

    await progress_bar.update()
    cluster.description = description
    cluster.name = title

    return cluster

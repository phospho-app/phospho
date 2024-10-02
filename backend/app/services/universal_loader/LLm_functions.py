from app.services.universal_loader.models import (
    OpenAI_Dataset_Format,
    Phospho_Dataset_Format,
    User_assistant,
)
import pandas as pd  # type: ignore
from app.core import config
from openai import OpenAI


def openai_converter(df: pd.DataFrame) -> OpenAI_Dataset_Format:
    columns_names = df.columns
    first_row = df.iloc[0]
    second_row = df.iloc[1]

    openai_client = OpenAI(
        api_key=config.OPENAI_API_KEY,
    )

    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that helps map CSV columns to a required format.",
            },
            {
                "role": "user",
                "content": f"""
    The following CSV columns are available: {columns_names}. Please try to map them to the required OpenAI_Dataset_Format columns.

    To help you, I will provide the content of the first two rows of the CSV file:
    The content of the first row is: {first_row}.
    The content of the second row is: {second_row}.
    Please, do not put the content of the rows in the OpenAI_Dataset_Format columns.

    Here are the required columns for the OpenAI_Dataset_Format:

    - content: The main text or message content.
    - role: The role of the user (e.g., system, assistant, user).
    - createdAt: The timestamp when the message was created.
    - conversationId: A unique identifier for the conversation.

    Please map the required columns (content, role, createdAt, conversationId) in OpenAI_Dataset_Format to the given CSV columns {columns_names}. If any of the required columns are missing from the CSV, indicate that as well. Provide the mapped column names and note any missing mappings.
            """,
            },
        ],
        response_format=OpenAI_Dataset_Format,
    )

    mapping = completion.choices[0].message.parsed

    if mapping is None:
        return OpenAI_Dataset_Format(
            content=None,
            role=None,
            createdAt=None,
            conversationId=None,
        )

    return mapping


def user_assistant_converter(df: pd.DataFrame) -> User_assistant:
    column = df["role"][:10]

    openai_client = OpenAI(
        api_key=config.OPENAI_API_KEY,
    )

    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that helps map the content of a CSV columns to a required format.",
            },
            {
                "role": "user",
                "content": f"""
    The following CSV column is available: {column}.

    Here are the User_assistant format:

    - assistant: The role of the assistant.
    - user: The role of the user.

    Please map the "user" and "assistant" role to the role in the given CSV column {column}. If any of the required columns are missing from the CSV, indicate that as well.
            """,
            },
        ],
        response_format=User_assistant,
    )

    mapping = completion.choices[0].message.parsed

    if mapping is None:
        return User_assistant(
            assistant=None,
            user=None,
        )

    return mapping


def phospho_converter(df: pd.DataFrame) -> Phospho_Dataset_Format:
    columns_names = df.columns
    first_row = df.iloc[0]
    second_row = df.iloc[1]

    openai_client = OpenAI(
        api_key=config.OPENAI_API_KEY,
    )

    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that helps map CSV columns to a required format.",
            },
            {
                "role": "user",
                "content": f"""
    The following CSV columns are available: {columns_names}. Please try to map them to the required Phospho_Dataset_Format columns.

    To help you, I will provide the content of the first two rows of the CSV file:
    The content of the first row is: {first_row}.
    The content of the second row is: {second_row}.
    Please, do not put the content of the rows in the Phospho_Dataset_Format columns.

    Here are the required columns for the Phospho_Dataset_Format:

    - input: The input text or data.
    - output: The output text or data.
    - created_at: The timestamp when the task was created.
    - task_id: A unique identifier for the task.
    - session_id: A unique identifier for the session.

    Please determine if each of the required columns in Phospho_Dataset_Format can be mapped to the given CSV columns. If any of the required columns are missing from the CSV, indicate that as well. Provide the mapped column names and note any missing mappings.
            """,
            },
        ],
        response_format=Phospho_Dataset_Format,
    )

    mapping = completion.choices[0].message.parsed

    if mapping is None:
        return Phospho_Dataset_Format(
            input=None,
            output=None,
            created_at=None,
            task_id=None,
            session_id=None,
        )

    return mapping

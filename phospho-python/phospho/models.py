"""
All the models stored in database.
"""

import datetime
import json
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_serializer

from phospho.utils import (
    generate_timestamp,
    generate_uuid,
    shorten_text,
)

# Add other job types here
RecipeType = Literal[
    "event_detection",
    "sentiment_language",
]


class ResultType(str, Enum):
    error = "error"
    bool = "bool"
    literal = "literal"
    list = "list"
    dict = "dict"
    string = "string"
    number = "number"
    object = "object"


class DatedBaseModel(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)


class ProjectElementBaseModel(DatedBaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    org_id: Optional[str] = None
    project_id: str


class EvaluationModelDefinition(BaseModel):
    project_id: str
    system_prompt: str


class EvaluationModel(EvaluationModelDefinition):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    removed: bool = False


class Eval(ProjectElementBaseModel):
    session_id: Optional[str] = None
    task_id: str
    # Flag to indicate if the task is success or failure
    value: Optional[Literal["success", "failure", "undefined"]]
    # The source of the event (either "user" or "phospho-{id}")
    source: str
    test_id: Optional[str] = None
    notes: Optional[str] = None
    task: Optional["Task"] = None
    evaluation_model: Optional[EvaluationModel] = None


DetectionScope = Literal[
    "task",
    "session",
    "task_input_only",
    "task_output_only",
    "system_prompt",
]

DetectionEngine = Literal[
    "llm_detection",
    "keyword_detection",
    "regex_detection",
]


class ScoreRangeSettings(BaseModel):
    min: float = 0
    max: float = 1
    score_type: Literal["confidence", "range", "category"] = "confidence"
    categories: Optional[List[str]] = None


class EventDefinition(DatedBaseModel):
    org_id: Optional[str] = None
    project_id: Optional[str] = None
    event_version_id: Optional[int] = None
    event_name: str
    description: str
    webhook: Optional[str] = None
    webhook_headers: Optional[dict] = None
    detection_engine: DetectionEngine = "llm_detection"
    detection_scope: DetectionScope = "task"
    keywords: Optional[str] = None
    regex_pattern: Optional[str] = None
    recipe_id: Optional[str] = None  # Associated Recipe id
    recipe_type: RecipeType = "event_detection"
    removed: bool = False
    score_range_settings: ScoreRangeSettings = Field(default_factory=ScoreRangeSettings)
    # If true, the event can only be detected in the last task of a session
    is_last_task: bool = False


class ScoreRange(BaseModel):
    score_type: Literal["confidence", "range", "category"]
    value: float
    min: float
    max: float
    label: Optional[str] = None
    options_confidence: Optional[Dict[Any, float]] = None
    # If the score is a category or a range, and the user labels the event manually,
    # the label is stored in corrected_label or corrected_value
    corrected_label: Optional[str] = None
    corrected_value: Optional[float] = None


class Event(ProjectElementBaseModel):
    # The name of the event (as defined in the project settings)
    event_name: str
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    # The webhook that was called (happened if the event was True and the webhook was set in settings)
    webhook: Optional[str] = None
    # The source of the event (either "user" or "phospho-{id}")
    source: str
    event_definition: Optional[EventDefinition] = None
    task: Optional["Task"] = None
    messages: Optional[List["Message"]] = Field(default_factory=list)
    removal_reason: Optional[str] = None
    removed: bool = False
    score_range: Optional[ScoreRange] = None
    confirmed: bool = False


class SentimentObject(BaseModel):
    score: Optional[float] = None
    magnitude: Optional[float] = None
    label: Optional[str] = None


class HumanEval(DatedBaseModel):
    flag: Optional[str] = None


class Task(ProjectElementBaseModel):
    session_id: Optional[str] = None
    input: str
    additional_input: Optional[dict] = Field(default_factory=dict)
    output: Optional[str] = None
    additional_output: Optional[dict] = Field(default_factory=dict)
    metadata: Optional[dict] = Field(default_factory=dict)
    data: Optional[dict] = Field(default_factory=dict)
    # Flag to indicate if the task is success or failure
    flag: Optional[str] = None  # Literal["success", "failure", "undefined"]
    last_eval: Optional[Eval] = None
    human_eval: Optional[HumanEval] = None
    sentiment: Optional[SentimentObject] = None
    language: Optional[str] = None
    # Events are stored in a subcollection of the task document
    events: Optional[List[Event]] = Field(default_factory=list)
    # The environment is a label
    # Deprecated
    environment: str = Field(default="default environment")
    # Notes are a free text field that can be edited
    notes: Optional[str] = None
    # Testing
    test_id: Optional[str] = None
    # Deprecated
    topics: Optional[List[str]] = Field(default=None)
    # Position of the task in the session
    task_position: Optional[int] = None
    is_last_task: Optional[bool] = None

    def preview(self) -> str:
        # Return a string representation of the input and output
        # This is used to display a preview of the task in the frontend
        if self.output is not None:
            # We only display the first 10 words of the input and output
            return f"{' '.join(self.input.split(' ')[:10]) + '...' if len(self.input.split(' ')) > 10 else self.input} -> {' '.join(self.output.split(' ')[:10]) + '...' if len(self.output.split(' ')) > 10 else self.output}"
        else:
            return f"{' '.join(self.input.split(' ')[:10]) + '...' if len(self.input.split(' ')) > 10 else self.input}"

    @field_serializer("metadata")
    def serialize_metadata(self, metadata: dict, _info):
        return json.loads(json.dumps(metadata, default=str))


class SessionStats(BaseModel):
    """
    Statistics computed at the session granularity,
    based on the Session content.
    """

    avg_sentiment_score: Optional[float] = None
    avg_magnitude_score: Optional[float] = None
    most_common_sentiment_label: Optional[str] = None
    most_common_language: Optional[str] = None
    most_common_flag: Optional[str] = None
    human_eval: Optional[str] = None


class Session(ProjectElementBaseModel):
    metadata: Optional[dict] = None
    data: Optional[dict] = None
    # Notes are a free text field that can be edited
    notes: Optional[str] = None
    # preview contains the first few tasks of the session
    preview: Optional[str] = None
    # The environment is a label
    environment: str = "default environment"
    events: Optional[List[Event]] = Field(default_factory=list)
    tasks: Optional[List[Task]] = None
    # Session length is computed dynamically. It may be None if not computed
    session_length: int = 0
    stats: SessionStats = Field(default_factory=SessionStats)
    last_message_ts: Optional[int] = None

    @field_serializer("metadata")
    def serialize_metadata(self, metadata: dict, _info):
        return json.loads(json.dumps(metadata, default=str))


class Threshold(BaseModel):
    score: Optional[float] = None
    magnitude: Optional[float] = None


class AnalyticsQuery(BaseModel):
    """Represents a query to run analytics on the data."""

    project_id: str
    collection: Literal[
        "events",
        "job_results",
        "private-clusters",
        "private-embeddings",
        "sessions",
        "tasks",
    ]
    aggregation_operation: Literal["count", "sum", "avg", "min", "max"]
    aggregation_field: Optional[str] = None  # Not required for count
    dimensions: List[str] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)
    sort: Dict[str, int] = Field(default_factory=dict)
    limit: int = 1000


class DashboardTile(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    tile_name: str
    metric: str
    breakdown_by: str
    metadata_metric: Optional[str] = None
    scorer_id: Optional[str] = None
    # Position
    x: Optional[int] = None
    y: Optional[int] = None
    w: int = 4
    h: int = 2


class ProjectSettings(BaseModel):
    events: Dict[str, EventDefinition] = Field(default_factory=dict)
    sentiment_threshold: Optional[Threshold] = Field(default_factory=Threshold)
    last_langsmith_extract: Optional[Union[str, datetime.datetime]] = None
    last_langfuse_extract: Optional[Union[str, datetime.datetime]] = None
    run_evals: Optional[bool] = False
    run_sentiment: Optional[bool] = True
    run_language: Optional[bool] = True
    run_event_detection: Optional[bool] = True
    ab_version_id: Optional[str] = "First version"
    dashboard_tiles: List[DashboardTile] = Field(
        default_factory=lambda: [
            DashboardTile(
                tile_name="Human rating per message position",
                metric="avg_success_rate",
                breakdown_by="task_position",
            ),
            DashboardTile(
                tile_name="Average human rating per event name",
                metric="avg_success_rate",
                breakdown_by="tagger_name",
            ),
            DashboardTile(
                tile_name="Average sentiment score per message position",
                metric="Avg",
                metadata_metric="sentiment_score",
                breakdown_by="task_position",
            ),
            DashboardTile(
                tile_name="Human rating per language",
                metric="avg_success_rate",
                breakdown_by="language",
            ),
        ]
    )
    analytics_threshold_enabled: bool = False
    analytics_threshold: int = 100_000


class Project(DatedBaseModel):
    org_id: str
    project_name: str  # to validate this, use https://docs.pydantic.dev/latest/concepts/validators/
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    user_id: Optional[str] = None

    @classmethod
    def from_previous(cls, project_data: dict) -> "Project":
        # Handle different names of the same field
        if "creation_date" in project_data.keys():
            project_data["created_at"] = project_data["creation_date"]

        if "id" not in project_data.keys():
            project_data["id"] = project_data["_id"]

        if "org_id" not in project_data.keys():
            raise ValueError("org_id is required in project_data")

        if "settings" in project_data.keys():
            # If event_name not in project_data.settings.events.values(), add it based on the key
            if "events" in project_data["settings"].keys():
                for event_name, event in project_data["settings"]["events"].items():
                    if "event_name" not in event.keys():
                        project_data["settings"]["events"][event_name]["event_name"] = (
                            event_name
                        )
                    if "org_id" not in event.keys():
                        project_data["settings"]["events"][event_name]["org_id"] = (
                            project_data["org_id"]
                        )
                    if "project_id" not in event.keys():
                        project_data["settings"]["events"][event_name]["project_id"] = (
                            project_data["id"]
                        )

            # Transition dashboard_tiles to lowercase and new fields
            if "dashboard_tiles" in project_data["settings"].keys():
                if project_data["settings"]["dashboard_tiles"] is None:
                    del project_data["settings"]["dashboard_tiles"]
                elif isinstance(project_data["settings"]["dashboard_tiles"], list):
                    # Rename the dashboard_tiles breakdown_by and metric fields
                    old_to_new_fields = {
                        # metric
                        "nb tasks": "nb_messages",
                        "nb sessions": "nb_sessions",
                        "event count": "tags_count",
                        "event distribution": "tags_distribution",
                        "avg success rate": "avg_success_rate",
                        "avg session length": "avg_session_length",
                        # breakdown_by
                        "event name": "tagger_name",
                        "event_name": "tagger_name",
                    }
                    for tile in project_data["settings"]["dashboard_tiles"]:
                        # Replace by a lowercase version of the field
                        tile["metric"] = tile["metric"].lower()
                        tile["breakdown_by"] = tile["breakdown_by"].lower()
                        # Replace the old fields by the new ones
                        tile["metric"] = old_to_new_fields.get(
                            tile["metric"], tile["metric"]
                        )
                        tile["breakdown_by"] = old_to_new_fields.get(
                            tile["breakdown_by"], tile["breakdown_by"]
                        )

        return cls(**project_data)


class LlmCall(DatedBaseModel, extra="allow"):
    project_id: Optional[str] = None
    org_id: Optional[str] = None
    model: str
    prompt: str
    llm_output: Optional[str] = None
    api_call_time: float  # In seconds
    # Identifier of the source of the evaluation, with the version of the model if phospho
    evaluation_source: Optional[str] = None
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    job_id: Optional[str] = None
    recipe_id: Optional[str] = None
    system_prompt: Optional[str] = None


class FlattenedTask(BaseModel, extra="allow"):
    task_id: str
    task_input: Optional[str] = None
    task_output: Optional[str] = None
    task_metadata: Optional[dict] = None
    task_eval: Optional[Literal["success", "failure"]] = None
    task_eval_source: Optional[str] = None
    task_eval_at: Optional[int] = None
    task_created_at: Optional[int] = None
    task_position: Optional[int] = None
    session_id: Optional[str] = None
    session_length: Optional[int] = None
    event_name: Optional[str] = None
    event_created_at: Optional[int] = None
    event_removal_reason: Optional[str] = None
    event_removed: Optional[bool] = None
    event_confirmed: Optional[bool] = None
    event_score_range_value: Optional[float] = None
    event_score_range_min: Optional[float] = None
    event_score_range_max: Optional[float] = None
    event_score_range_score_type: Optional[
        Literal["confidence", "range", "category"]
    ] = None
    event_score_range_label: Optional[str] = None
    event_source: Optional[str] = None
    event_categories: Optional[List[str]] = None


class DatasetRow(DatedBaseModel, extra="allow"):
    org_id: str
    file_id: str  # Generated on the fly when the file is uploaded to the API
    file_name: Optional[str] = None
    # Then any information in the dataset is stored as an extra field


class FineTuningJob(DatedBaseModel, extra="allow"):
    id: str = Field(default_factory=lambda: generate_uuid("ftjob_"))
    org_id: str
    # File id used for the fine-tuning (will be splitted in train and validation sets)
    file_id: str
    # The name of the fine-tuned model that is being created. Null if the fine-tuning job is still running.
    fine_tuned_model: Optional[str] = None
    finished_at: Optional[int] = None
    # Storing parameters for the fine-tuning job, also detection_scope, event_description
    parameters: Optional[dict] = Field(default_factory=dict)
    model: str  # The base model that is being fine-tuned.
    status: Literal["started", "finished", "failed", "cancelled"]


class Message(DatedBaseModel):
    role: Optional[str] = None
    content: str
    previous_messages: List["Message"] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    def as_list(self):
        """
        Return the message and its previous messages as a list of Message objects.
        """
        if self.previous_messages:
            return self.previous_messages + [self]
        else:
            return [self]

    def transcript(
        self,
        with_role: bool = True,
        with_previous_messages: bool = False,
        only_previous_messages: bool = False,
        max_previous_messages: Optional[int] = None,
        message_content_max_len: Optional[int] = None,
        message_content_shorten_how: Literal["left", "right", "center"] = "left",
    ) -> str:
        """
        Return a string representation of the message.
        """
        transcript = ""
        if max_previous_messages is not None:
            if max_previous_messages > len(self.previous_messages):
                max_previous_messages = len(self.previous_messages)
            if max_previous_messages < 0:
                max_previous_messages = 0
            previous_messages = self.previous_messages[-max_previous_messages:]
        else:
            previous_messages = self.previous_messages

        if with_previous_messages:
            transcript += "\n".join(
                [
                    message.transcript(with_role=with_role)
                    for message in previous_messages
                ]
            )
        if not only_previous_messages:
            if with_role:
                transcript += f"{self.role}: {self.content}"
            else:
                if message_content_max_len is not None:
                    content = shorten_text(
                        prompt=self.content,
                        max_length=message_content_max_len,
                        how=message_content_shorten_how,
                    )
                else:
                    content = self.content
                transcript += "\n" + content
        return transcript

    def previous_messages_transcript(
        self,
        with_role: bool = True,
    ) -> Optional[str]:
        """
        Return a string representation of the message.
        """
        if len(self.previous_messages) == 0:
            return None
        return self.transcript(
            with_role=with_role,
            with_previous_messages=True,
            only_previous_messages=True,
        )

    def latest_interaction(self) -> str:
        """
        Return the latest interaction of the message
        """
        # Latest interaction is the last message of the previous messages
        # And the message itself
        if len(self.previous_messages) == 0:
            return self.transcript(with_role=True)
        else:
            return "\n".join(
                [
                    self.previous_messages[-1].transcript(with_role=True),
                    self.transcript(with_role=True),
                ]
            )

    def latest_interaction_context(self) -> Optional[str]:
        """
        Return the context of the latest interaction, aka
        the n-2 previous messages until n-1 and message.
        """
        if len(self.previous_messages) <= 1:
            return None
        else:
            return "\n".join(
                [
                    message.transcript(with_role=True)
                    for message in self.previous_messages[:-1]
                ]
            )

    @classmethod
    def from_df(cls, df, **kwargs) -> List["Message"]:
        """
        Create a list of Message objects from a pandas DataFrame.

        ```python
        import pandas as pd

        df = pd.DataFrame({
            "content": ["Hello", "How are you?"],
            "context_role": ["user", "assistant"],
        })

        messages = Message.from_df(df, role="context_role)
        ```

        :param df: The DataFrame to convert to a list of Message objects
        :param kwargs: The mapping from the Message fields to the column names of the DataFrame.
            Supported fields are: id, created_at, role, content, previous_messages, metadata.
            - The only required field is "content". Other fields are optional.
            - If not provided, a default mapping is used, where the field name is the same as the column name.
            - If the mapping refers to an unknown column name, a ValueError is raised.
            - Pass None to a field to skip it and use a default value.

        :return: A list of Message objects
        """
        try:
            import pandas as pd  # type: ignore
        except ImportError:
            raise ImportError("Pandas is required to use the from_df method")

        # The keyword arguments are understood as mapping from the Message
        # fields to the column names of the DataFrame
        # If not provided, the default mapping is used
        default_mapping: Dict[str, object] = {
            "id": None,
            "created_at": "created_at",
            "role": "role",
            "content": "content",
            "previous_messages": "previous_messages",
            "metadata": "metadata",
        }
        # If a default mapping value is not found in the DataFrame, it is skipped
        for key, value in default_mapping.items():
            if value not in df.columns:
                default_mapping[key] = None
        # If a kwargs refers to an unknwon column name, raise a ValueError
        for key, value in kwargs.items():
            if value not in df.columns and value is not None:
                raise ValueError(f"Column {value} not found in the DataFrame")

        col_mapping = {**default_mapping, **kwargs}

        # Verify that mandatory field are present. If not, raise a ValueError
        if col_mapping["content"] is None:
            raise ValueError(
                'Column "content" not found in the DataFrame. '
                + 'Please provide a keyword argument with the column to use: `Message.from_df(df, content="message_content")`.'
            )

        # Convert every row of the df into a lab.Message
        messages = []
        for index, row in df.iterrows():
            content = row[col_mapping["content"]]
            if content and not pd.isnull(content):
                values_to_create_message = {}
                for attribute, col_name in col_mapping.items():
                    if col_name is not None:
                        values_to_create_message[attribute] = row[col_name]
                if col_mapping["id"] is None:
                    # By default, the id is the index of the row
                    message_id = str(index)
                else:
                    message_id = row[col_mapping["id"]]
                message_dict = {
                    **values_to_create_message,
                    "id": message_id,
                    "content": content,
                }
                messages.append(cls(**message_dict))

        return messages

    @classmethod
    def from_task(
        cls,
        task: Task,
        previous_tasks: Optional[List[Task]] = None,
        metadata: Optional[dict] = None,
        ignore_last_output: bool = False,
    ) -> "Message":
        """
        Create a Message from a Task object.

        The Message object is created from the input and output of the Task object.
        If the Task object has previous tasks, the Message object will contain
        the input and output of the previous tasks as well.

        :return: A list of Message objects
        """
        if metadata is None:
            metadata = {}
        if previous_tasks is None:
            previous_tasks = []

        # Add the task to the metadata
        metadata["task"] = task

        previous_messages: List["Message"] = []
        for i, previous_task in enumerate(previous_tasks):
            previous_messages.append(
                cls(
                    id="input_" + previous_task.id,
                    role="user",
                    content=previous_task.input,
                )
            )
            if previous_task.output is not None:
                previous_messages.append(
                    cls(
                        id="output_" + previous_task.id,
                        role="assistant",
                        content=previous_task.output,
                    )
                )

        if ignore_last_output:
            task.output = None

        if task.output is not None:
            previous_messages.append(
                cls(
                    id="input_" + task.id,
                    role="user",
                    content=task.input,
                )
            )
            message = cls(
                id="output_" + task.id,
                role="assistant",
                content=task.output,
                previous_messages=previous_messages,
                metadata=metadata,
            )
        else:
            message = cls(
                id="input_" + task.id,
                role="user",
                content=task.input,
                previous_messages=previous_messages,
                metadata=metadata,
            )

        return message

    @classmethod
    def from_session(
        cls, session: Session, metadata: Optional[dict] = None
    ) -> "Message":
        """
        Create a list of Message objects from a Session object.

        :param session: The Session object to convert to a list of Message objects

        :return: A list of Message objects
        """
        if session.tasks is None or len(session.tasks) == 0:
            raise ValueError("The session does not contain any task")
        task = session.tasks[-1]
        if len(session.tasks) == 1:
            previous_tasks = []
        else:
            previous_tasks = session.tasks[:-1]
        return cls.from_task(
            task=task, previous_tasks=previous_tasks, metadata=metadata
        )


class Recipe(ProjectElementBaseModel):
    status: Literal["enabled", "deleted"] = "enabled"
    recipe_type: RecipeType
    # Parameters for the job, for instance it was the event object in the settings
    parameters: dict = Field(default_factory=dict)


class JobResult(DatedBaseModel, extra="allow"):
    org_id: Optional[str] = None
    project_id: Optional[str] = None
    job_id: Optional[str] = None
    job_metadata: dict = Field(default_factory=dict)
    value: Any
    result_type: ResultType
    logs: List[Any] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    task_id: Optional[str] = None


class ProjectDataFilters(BaseModel):
    """
    This is a model used to filter tasks, sessions or events in
    different endpoints.
    """

    created_at_start: Optional[Union[int, datetime.datetime]] = None
    created_at_end: Optional[Union[int, datetime.datetime]] = None
    event_name: Optional[List[str]] = None
    event_id: Optional[List[str]] = None
    flag: Optional[str] = None
    scorer_value: Optional[Dict[str, float]] = None
    classifier_value: Optional[Dict[str, str]] = None
    metadata: Optional[dict] = None
    user_id: Optional[str] = None
    last_eval_source: Optional[str] = None
    sentiment: Optional[str] = None
    language: Optional[str] = None
    has_notes: Optional[bool] = None
    tasks_ids: Optional[List[str]] = None
    clustering_id: Optional[str] = None  # A group of clusters
    clusters_ids: Optional[List[str]] = None  # A list of clusters
    is_last_task: Optional[bool] = None
    sessions_ids: Optional[List[str]] = None
    version_id: Optional[str] = None
    task_position: Optional[int] = None


class Cluster(ProjectElementBaseModel):
    model: Literal["intent-embed", "intent-embed-2", "intent-embed-3"] = "intent-embed"
    clustering_id: str  # all the clusters in the same cluster have the same
    name: str  # group name
    description: str  # generated by AI
    size: int  # $size of tasks_id
    # reference to the tasks in the cluster
    tasks_ids: Optional[List[str]] = None
    # reference to the sessions in the cluster
    sessions_ids: Optional[List[str]] = None
    scope: Optional[Literal["messages", "sessions", "users"]] = None
    embeddings_ids: Optional[List[str]] = None


class Clustering(ProjectElementBaseModel):
    model: Literal["intent-embed", "intent-embed-2", "intent-embed-3"] = "intent-embed"
    type: Optional[str] = None
    nb_clusters: Optional[int] = None
    clusters_ids: List[str]
    status: Optional[
        Literal[
            "started",
            "loading_existing_embeddings",
            "generating_new_embeddings",
            "generate_clusters",
            "generate_clusters_description_and_title",
            "merging_similar_clusters",
            "saving_clusters",
            "summaries",
            "completed",
        ]
    ] = None
    percent_of_completion: Optional[float] = None  # 0-100
    clusters: Optional[List[Cluster]] = None
    scope: Optional[Literal["messages", "sessions", "users"]] = None
    clustering_mode: Literal["agglomerative", "dbscan"] = "agglomerative"
    name: Optional[str] = None
    instruction: Optional[str] = None
    pca: Optional[dict] = None
    tsne: Optional[dict] = None


class UsageQuota(BaseModel):
    org_id: str
    plan: str
    current_usage: int
    max_usage: Optional[int]
    max_usage_label: str
    balance_transaction: Optional[float] = None
    next_invoice_total: Optional[float] = None  # BEFORE discount (free credits)
    next_invoice_amount_due: Optional[float] = None  # AFTER discount (free credits)
    customer_id: Optional[str] = None  # Stripe customer_id


class PipelineResults(BaseModel):
    """
    The results of a pipeline execution. Contains every category of analytics.

    Each category of analytics is a dict linking the message_id or task_id
    to the analytics object. This is useful for batching and unordered processing.
    """

    events: Dict[str, List[Event]] = Field(
        default_factory=dict, description="Events detected in the messages"
    )
    # Deprecated
    flag: Optional[Dict[str, Literal["success", "failure"]]] = Field(
        default_factory=dict,
        description="Flag of the task: success or failure.",
    )
    language: Dict[str, Optional[str]] = Field(
        default_factory=dict, description="Language detected in the messages."
    )
    sentiment: Dict[str, Optional[SentimentObject]] = Field(
        default_factory=dict, description="Sentiment detected in the messages."
    )

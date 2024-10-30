from typing import Dict, List, Optional
from loguru import logger
from pydantic import BaseModel

from app.db.mongo import get_mongo_db
from opentelemetry.proto.trace.v1.trace_pb2 import TracesData
from google.protobuf.json_format import MessageToDict
from google.protobuf.internal.containers import RepeatedCompositeFieldContainer
from opentelemetry.proto.common.v1.common_pb2 import KeyValue


class StandardSpanModel(BaseModel):
    org_id: str
    project_id: str
    task_id: str
    session_id: str
    metadata: Optional[dict] = None
    #
    propagate: Optional[bool] = None
    #
    start_time_unix_nano: int
    end_time_unix_nano: int
    open_telemetry_data: dict
    # In open_telemetry_data, you have a gen_ai key: https://opentelemetry.io/docs/specs/semconv/attributes-registry/gen-ai/


class OpenTelemetryConnector:
    project_id: str
    org_id: str

    def __init__(self, org_id: str, project_id: str):
        self.project_id = project_id
        self.org_id = org_id

    async def _dump(self, data: TracesData) -> None:
        """
        Store the raw data in the database
        """
        mongo_db = await get_mongo_db()
        # Convert the data to a dictionary
        data_dict = MessageToDict(data)
        mongo_db["logs_opentelemetry"].insert_one(data_dict)

    def _convert_attributes(
        self, attributes: RepeatedCompositeFieldContainer[KeyValue]
    ) -> dict:
        # Unpack attributes
        unpacked_attributes: dict = {}
        for attr in attributes:
            # Convert to a dictionary
            k = attr.key
            attr_dict = MessageToDict(attr)

            if "stringValue" in attr_dict["value"]:
                value = attr_dict["value"]["stringValue"]
            elif "intValue" in attr_dict["value"]:
                value = attr_dict["value"]["intValue"]
            elif "boolValue" in attr_dict["value"]:
                value = attr_dict["value"]["boolValue"]
            elif "doubleValue" in attr_dict["value"]:
                value = attr_dict["value"]["doubleValue"]
            elif "arrayValue" in attr_dict["value"]:
                value = attr_dict["value"]["arrayValue"]
            else:
                logger.error(f"Unknown value type: {attr_dict}")
                continue

            # Merge the nested attributes
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

        return unpacked_attributes

    async def process(self, data: TracesData) -> int:
        """
        Push the data and process it
        """
        logger.info(f"Processing OpenTelemetry data:\n{data}")
        # Start by storing the raw data, for debug purposes
        await self._dump(data)

        # List of all processed spans
        all_spans: List[dict] = []

        for resource in data.resource_spans:
            scope_spans = resource.scope_spans
            for scope in scope_spans:
                for span in scope.spans:
                    span_task_id = None
                    span_session_id = None
                    span_metadata = None
                    span_propagate = False

                    unpacked_attributes = self._convert_attributes(span.attributes)
                    # Convert the span to a dictionary and replace attributes with the unpacked ones
                    span_to_store = MessageToDict(span)
                    span_to_store["attributes"] = unpacked_attributes

                    logger.info(f"Found attributes: {unpacked_attributes}")

                    # Look for the task_id and session_id in the attributes
                    if "phospho" in unpacked_attributes:
                        span_task_id = unpacked_attributes["phospho"].get("task_id")
                        span_session_id = unpacked_attributes["phospho"].get(
                            "session_id"
                        )
                        span_metadata = unpacked_attributes["phospho"].get("metadata")
                        span_propagate = unpacked_attributes["phospho"].get("propagate")

                    all_spans.append(
                        {
                            "org_id": self.org_id,
                            "project_id": self.project_id,
                            "open_telemetry_data": span_to_store,
                            "task_id": span_task_id,
                            "session_id": span_session_id,
                            "metadata": span_metadata,
                            "start_time_unix_nano": span.start_time_unix_nano,
                            "end_time_unix_nano": span.end_time_unix_nano,
                            "propagate": span_propagate,
                        }
                    )

        logger.info(f"Found {len(all_spans)} spans to process.")

        # Sort the spans by reverse end_time_unix_nano (more recent first)
        all_spans.sort(key=lambda x: x["end_time_unix_nano"], reverse=True)

        for s in all_spans:
            logger.debug(s)

        # Either each span has a task_id and session_id, or we use the one in the latest span
        trace_task_id = None
        trace_session_id = None
        trace_metadata = None

        # Collect the spans to export in a new list
        spans_to_export = []

        for processed_span in all_spans:
            # If the span has a "propagate" attribute, propagate the task_id and session_id
            if processed_span["propagate"]:
                # Propagate the task_id and session_id to the next spans
                trace_task_id = processed_span["task_id"]
                trace_session_id = processed_span["session_id"]
                trace_metadata = processed_span["metadata"]
            # If the task_id and session_id are not set, use the ones from the trace
            if processed_span["task_id"] is None:
                processed_span["task_id"] = trace_task_id
            if processed_span["session_id"] is None:
                processed_span["session_id"] = trace_session_id
            if processed_span["metadata"] is None:
                processed_span["metadata"] = trace_metadata

            # Only log open_telemetry_data which have a gen_ai attribute
            # TODO: Change this criterion to store more kind of spans
            if "gen_ai" in processed_span["open_telemetry_data"]["attributes"]:
                spans_to_export.append(processed_span)

        # Store the spans in the database
        if spans_to_export:
            logger.info(f"Opentelemetry: Storing {len(spans_to_export)} in db")
            mongo_db = await get_mongo_db()
            mongo_db["opentelemetry"].insert_many(spans_to_export)

        return 0


async def fetch_spans_for_task(
    project_id: str, task_id: str
) -> List[StandardSpanModel]:
    """
    Fetch all the spans linked to a task_id
    """

    mongo_db = await get_mongo_db()

    spans = (
        await mongo_db["opentelemetry"]
        .find({"project_id": project_id, "task_id": task_id})
        .to_list(None)
    )
    # Filter _id field
    valid_spans = []
    for span in spans:
        span.pop("_id")
        try:
            valid_spans.append(StandardSpanModel.model_validate(span))
        except Exception as e:
            logger.error(f"Error validating span: {e}")

    return spans

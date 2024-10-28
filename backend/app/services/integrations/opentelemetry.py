from loguru import logger

from app.db.mongo import get_mongo_db
from opentelemetry.proto.trace.v1.trace_pb2 import TracesData
from google.protobuf.json_format import MessageToDict


class OpenTelemetryConnector:
    project_id: str
    org_id: str

    def __init__(self, org_id: str, project_id: str):
        self.project_id = project_id
        self.org_id = org_id

    async def _dump(self, data: dict) -> None:
        """
        Store the raw data in the database
        """
        mongo_db = await get_mongo_db()
        mongo_db["logs_opentelemetry"].insert_one(data)

    async def process(self, data: TracesData) -> int:
        """
        Push the data and process it
        """
        logger.info(f"Processing OpenTelemetry data:\n{data}")

        # Convert the data to a dictionary
        data_as_dict = MessageToDict(data)

        await self._dump(data_as_dict)
        try:
            # TODO: Find better way of doing this
            resource_spans = data.resource_spans

            for resource in resource_spans:
                scope_spans = resource.scope_spans
                for scope in scope_spans:
                    for span in scope.spans:
                        # Unpack attributes
                        attributes = span.attributes
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
                                        current_dict = current_dict[key][
                                            int(keys[i + 1])
                                        ]
                                    except IndexError:
                                        logger.error(
                                            f"IndexError: {key} {keys[i + 1]} {current_dict[key]}"
                                        )
                                        continue
                                else:
                                    current_dict = current_dict[key]
                            current_dict[keys[-1]] = value

                        span_to_store = MessageToDict(span)
                        span_to_store["attributes"] = unpacked_attributes

                        # We only keep the spans that have the "gen_ai.system" attribute
                        if "gen_ai" in unpacked_attributes:
                            mongo_db = await get_mongo_db()

                            # Store the data in the database
                            mongo_db["opentelemetry"].insert_one(
                                {
                                    "org_id": self.org_id,
                                    "project_id": self.project_id,
                                    "open_telemetry_data": span_to_store,
                                }
                            )
                            logger.info("Opentelemetry data stored in the database")

        except KeyError as e:
            logger.error(f"KeyError: {e}")

        return 0

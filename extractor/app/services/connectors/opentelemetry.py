from typing import Optional

from loguru import logger

from app.db.mongo import get_mongo_db
from app.services.connectors.base import BaseConnector


class OpenTelemetryConnector(BaseConnector):
    data: dict

    def __init__(self, project_id: str, data: dict):
        self.project_id = project_id
        self.data = data

    async def _dump(self):
        """
        Store the raw data in the database
        """
        mongo_db = await get_mongo_db()
        mongo_db["logs_opentelemetry"].insert_one(self.data)

    async def process(
        self,
        org_id: str,
        current_usage: int,
        max_usage: Optional[int] = None,
    ) -> int:
        """
        Push the data and process it
        """
        self._dump()
        try:
            # TODO: Find better way of doing this
            resource_spans = self.data["resourceSpans"]
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

            # We only keep the spans that have the "gen_ai.system" attribute
            if "gen_ai" in unpacked_attributes:
                mongo_db = await get_mongo_db()

                # Store the data in the database
                mongo_db["opentelemetry"].insert_one(
                    {
                        "org_id": org_id,
                        "project_id": self.project_id,
                        "open_telemetry_data": spans,
                    }
                )
                logger.info("Opentelemetry data stored in the database")

            # TODO: Implement the log processing

        except KeyError as e:
            logger.error(f"KeyError: {e}")

        return 0

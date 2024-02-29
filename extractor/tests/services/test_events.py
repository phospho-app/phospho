import pytest
from app.services.events import event_detection

import app.core.config as config

assert config.ENVIRONMENT != "production"


@pytest.mark.asyncio
async def test_event_detection(db, populated_project):
    async for mongo_db in db:
        # Example input
        task_transcript = """User : What is the weather like today?
        Assistant : The weather is sunny today."""
        event_name = "weather_request"
        event_description = "The user asks the assistant for the weather"
        task_context_transcript = ""

        # Call the function
        detected_event, evaluation_source = await event_detection(
            task_transcript,
            event_name,
            event_description,
            task_context_transcript,
            store_llm_call=True,
        )

        assert detected_event == True

        # Now, we wan't the event to be false
        task_transcript = """
        User : Order me some beers.
        Assistant : It's done.
        """
        event_name = "weather_request"
        event_description = "The user asks the assistant for the weather"
        task_context_transcript = ""

        # Call the function
        detected_event, evaluation_source = await event_detection(
            task_transcript,
            event_name,
            event_description,
            task_context_transcript,
            store_llm_call=True,
        )

        assert detected_event == False

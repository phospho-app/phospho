from google.cloud import language_v2
from phospho.models import SentimentObject
from loguru import logger
from google.oauth2 import service_account
import os
import json

try:
    credentials_dict = json.loads(os.getenv("GCP_JSON_CREDENTIALS"))
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict
    )
    client = language_v2.LanguageServiceClient(credentials=credentials)
    logger.info("Sentiment analysis active")
except Exception as e:
    logger.error(f"Error connecting to sentiment analysis: {e}")
    client = None


async def run_sentiment_analysis(
    text: str, language: str = "unknown"
) -> SentimentObject:
    """
    Analyzes Sentiment in a string.

    Args:
      text_content: The text content to analyze.
    """
    try:
        # Available types: PLAIN_TEXT, HTML
        document_type_in_plain_text = language_v2.Document.Type.PLAIN_TEXT

        # Optional. If not specified, the language is automatically detected.
        # For list of supported languages:
        # https://cloud.google.com/natural-language/docs/languages

        document = {
            "content": text,
            "type_": document_type_in_plain_text,
        }
        if language != "unknown":
            document["language_code"] = language

        # Available values: NONE, UTF8, UTF16, UTF32
        # See https://cloud.google.com/natural-language/docs/reference/rest/v2/EncodingType.

        encoding_type = language_v2.EncodingType.UTF8

        response = client.analyze_sentiment(
            request={"document": document, "encoding_type": encoding_type}
        )

        sentiment_response = SentimentObject(
            score=response.document_sentiment.score,
            magnitude=response.document_sentiment.magnitude,
            # sentences=response.sentences,
        )
        # We interpret the sentiment score as follows:
        if sentiment_response.score > 0.3:
            sentiment_response.label = "positive"
        elif sentiment_response.score < -0.3:
            sentiment_response.label = "negative"
        else:
            if sentiment_response.magnitude < 1:
                sentiment_response.label = "neutral"
            else:
                sentiment_response.label = "mixed"

    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")

        sentiment_response = SentimentObject()

    return sentiment_response

from typing import Optional
from google.cloud import language_v2
from phospho.models import SentimentObject
from loguru import logger
from google.oauth2 import service_account
import os
import json
from base64 import b64decode

client = None

try:
    credentials_natural_language = os.getenv(
        "GCP_JSON_CREDENTIALS_NATURAL_LANGUAGE_PROCESSING"
    )
    # TODO: this will fail in self-hosted environments
    if credentials_natural_language is not None:
        credentials_dict = json.loads(
            b64decode(credentials_natural_language).decode("utf-8")
        )
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict
        )
        client = language_v2.LanguageServiceClient(credentials=credentials)
        logger.info("Sentiment analysis active")
    else:
        logger.error("No GCP_JSON_CREDENTIALS environment variable found")

except Exception as e:
    logger.error(f"Error connecting to sentiment analysis: {e}")


async def call_sentiment_and_language_api(
    text: str, score_threshold: float, magnitude_threshold: float
) -> tuple[SentimentObject, Optional[str]]:
    """
    Analyzes Sentiment and Language of a given text.

    The sentiment object contains both a score and a magnitude.
    - score: positive values indicate positive sentiment, negative values indicate negative sentiment.
    - magnitude: the overall strength of emotion (both positive and negative) within the given text.

    Args:
      text_content: The text content to analyze.
    """
    if client is None:
        logger.warning("No client available for sentiment analysis")
        return SentimentObject(), None

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

        # Available values: NONE, UTF8, UTF16, UTF32
        # See https://cloud.google.com/natural-language/docs/reference/rest/v2/EncodingType.

        encoding_type = language_v2.EncodingType.UTF8

        response = client.analyze_sentiment(
            request={"document": document, "encoding_type": encoding_type}
        )

        sentiment_response = SentimentObject(
            score=response.document_sentiment.score,
            magnitude=response.document_sentiment.magnitude,
        )

        # We interpret the sentiment score as follows:
        if sentiment_response.score > score_threshold:
            sentiment_response.label = "positive"
        elif sentiment_response.score < -score_threshold:
            sentiment_response.label = "negative"
        else:
            if sentiment_response.magnitude < magnitude_threshold:
                sentiment_response.label = "neutral"
            else:
                sentiment_response.label = "mixed"

        language = response.language_code

    except Exception as e:
        if "Cannot determine the language of the document." in str(e):
            logger.info("Language not detected by Google API")
        else:
            logger.error(f"Error in sentiment analysis: {e}")

        sentiment_response = SentimentObject()
        language = None

    return sentiment_response, language

# import base64
# import json

# from google.cloud import language_v1
# from google.oauth2 import service_account

# from loguru import logger

# from app.core import config

# credentials_dict = config.GCP_JSON_CREDENTIALS

# # Create credentials from the service account info
# credentials = service_account.Credentials.from_service_account_info(credentials_dict)

# # Instantiates a client
# client = language_v1.LanguageServiceClient(credentials=credentials)

# def extract_topics(text_content: str, language: str = "en") -> list[str]:
#     """
#     TODO : make the Googla API call asynchronous
#     """
#     # Available types: PLAIN_TEXT, HTML
#     type_ = language_v1.Document.Type.PLAIN_TEXT

#     # Optional. If not specified, the language is automatically detected.
#     # For list of supported languages:
#     # https://cloud.google.com/natural-language/docs/languages
#     # TODO : add setup for other languages
#     document = {"content": text_content, "type_": type_, "language": language}

#     content_categories_version = (
#         language_v1.ClassificationModelOptions.V2Model.ContentCategoriesVersion.V2
#     )
#     response = client.classify_text(
#         request={
#             "document": document,
#             "classification_model_options": {
#                 "v2_model": {"content_categories_version": content_categories_version}
#             },
#         }
#     )
#     detected_topics = []

#     # Loop through classified categories returned from the API
#     for category in response.categories:
#         # Get the name of the category representing the document.
#         # See the predefined taxonomy of categories:
#         # https://cloud.google.com/natural-language/docs/categories
#         logger.debug(f"Category name: {category.name} with confidence {category.confidence}")
#         category_name = category.name

#         for topic in category_name.split("/"):
#             if topic not in detected_topics:
#                 if topic not in ["", "Other"]:
#                     detected_topics.append(topic)
#         # Get the confidence. Number representing how certain the classifier
#         # is that this category represents the provided text.

#     logger.debug("Detected topics:", detected_topics)
#     return detected_topics

import requests  # type: ignore
from loguru import logger


def trigger_webhook(
    url: str, json: dict, timeout: int = 1, headers: dict | None = None
):
    """
    Function to trigger a webhook.
    :param url: The URL to trigger the webhook on.
    :param data: The data to send to the webhook.
    :param timeout: The timeout for the request, an int in seconds.
    """
    # Filter empty values from the headers (where str is "")
    headers = {k: v for k, v in (headers or {}).items() if v is not None and v != ""}
    # If the url is not set, return early
    if url == "":
        logger.warning("No webhook URL set, skipping webhook trigger")
        return
    try:
        response = requests.post(url, json=json, timeout=timeout, headers=headers)
        response.raise_for_status()
        logger.info(f"Webhook triggered successfully: {response.status_code}")
        return response.text
    except requests.exceptions.Timeout:
        logger.debug(f"Request timed out when sending webhook to {url}")
    except requests.exceptions.HTTPError as err:
        logger.debug(f"HTTP error occurred when webhook {url}: {err}")
    except requests.exceptions.RequestException as err:
        logger.debug(f"A request exception occurred when webhook {url}: {err}")

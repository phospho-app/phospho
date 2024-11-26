import logging
import os

import functions_framework
import requests

logger = logging.getLogger(__name__)


def slack_notification(message: str) -> None:
    """Send slack notification to the channel

    The url to the channel is stored in the environment variable SLACK_URL"""
    url = os.environ["SLACK_URL"]
    if not url:
        logger.warning("SLACK_URL is not set, notification will not be sent")
        return

    data = {"text": message}
    response = requests.post(url, json=data)
    if response.status == 200:
        logger.info("Notification sent successfully")
    else:
        logger.warning(f"Failed to send notification, status code:{response.status}")


def test_api_endpoint(url: str, message: str) -> dict:
    # use the requests library to test the API endpoint
    # if the response is not 200, send a slack notification
    # if the response is 200, log a message
    try:
        response = requests.get(url)
        if response.status_code == 200:
            logger.info(f"{message} {url} successful")
        else:
            logger.error(f"{message} {url} failed:{response}")
            slack_notification(f"{message} failed:{response}")
            # Build a dictionary with the response status code and content
        return {
            "url": url,
            "status": "success" if response.status_code == 200 else "failed",
            "details": {
                "type": "status code",
                "status_code": response.status_code,
                "text": response.text,
            },
        }
    except Exception as e:
        logger.error(f"Calling {url} failed:{e}")
        return {
            "url": url,
            "status_code": "failed",
            "details": {
                "type": "exception",
                "exception": e,
            },
        }


@functions_framework.http
def lifecheck(request):
    """
    HTTP Cloud Function.
    """
    request.get_json(silent=True)

    test_platform = test_api_endpoint(
        "https://api.phospho.ai/api/health", "Phospho platform API healthcheck"
    )
    test_v2 = test_api_endpoint(
        "https://api.phospho.ai/v2/health", "Phospho platform API v2 healthcheck"
    )

    return {
        "platform": test_platform,
        "v2": test_v2,
    }

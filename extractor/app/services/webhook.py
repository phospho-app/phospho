from typing import Optional

import aiohttp
from loguru import logger


async def trigger_webhook(
    url: str, json: dict, timeout: int = 3, headers: Optional[dict] = None
):
    """
    Async function to trigger a webhook. Sends a POST request to the given URL
    with the given data.

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
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=json, timeout=timeout, headers=headers
            ) as response:
                response.raise_for_status()
                logger.info(f"Webhook triggered successfully: {response.status}")
                response_txt = await response.text()
        return response_txt
    except aiohttp.ClientError as e:
        logger.error(f"Error sending webhook to {url}: {e}")
        return None

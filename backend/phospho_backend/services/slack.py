import aiohttp
from loguru import logger
from phospho_backend.core import config


async def slack_notification(message: str, send_only_in_prod: bool = True) -> None:
    """Send slack notification to the channel

    The url to the channel is stored in the environment variable SLACK_URL"""
    url = config.SLACK_URL
    if not url:
        logger.warning("SLACK_URL is not set, notification will not be sent")
        return
    else:
        logger.debug(f"SLACK_URL: {url}")

    env = config.ENVIRONMENT

    if send_only_in_prod and (env != "production"):
        logger.info("Skipping slack notification because we are not in production")
        logger.debug(f"Message: {message}")
        return
    else:
        data = {"text": message}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    logger.info("Notification sent successfully")
                else:
                    logger.warning(
                        f"Failed to send notification, status code:{response.status}"
                    )


# Usage example
# import asyncio
# asyncio.run(slack_notification("Hello, World! Test slack notif from backend"))

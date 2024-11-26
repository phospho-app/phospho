import pytest

from phospho_backend.services.mongo.emails import (
    send_email,
    send_welcome_email,
    send_quota_exceeded_email,
)


@pytest.mark.asyncio
async def test_emails_service(db, populated_project):
    async for mongo_db in db:
        send_email(
            to_email="delivered@resend.dev",
            subject="Python Test",
            message="Hello from Python!",
        )
        assert True

        send_welcome_email("delivered@resend.dev")
        assert True

        await send_quota_exceeded_email(populated_project.org_id)

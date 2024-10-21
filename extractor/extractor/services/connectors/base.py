from typing import Optional


class BaseConnector:
    project_id: str

    def __init__(
        self,
        project_id: str,
    ):
        self.project_id = project_id

    async def load_config(self, **kwargs):
        """
        Load the configuration for the connector
        """
        return

    async def save_config(self, *args, **kwargs):
        """
        Register the configuration for the connector and the fact that it will be used
        """
        return

    async def _dump(self):
        """
        Dump the raw pulled data
        """
        raise NotImplementedError

    async def pull(self):
        """
        Pull the data
        """
        raise NotImplementedError

    async def process(
        self,
        org_id: str,
        current_usage: int,
        max_usage: Optional[int] = None,
    ) -> int:
        """
        Push the data and process it
        Return the number of logs processed
        """
        raise NotImplementedError

    async def sync(
        self,
        org_id: str,
        current_usage: int,
        max_usage: Optional[int] = None,
        **kwargs,
    ):
        await self.load_config(**kwargs)
        await self.pull()
        nb_job_results = await self.process(
            org_id=org_id,
            current_usage=current_usage,
            max_usage=max_usage,
        )
        await self.save_config(**kwargs)
        return {
            "status": "ok",
            "message": "Synchronisation pipeline ran successfully",
            "nb_job_results": nb_job_results,
            "action": "sync",
        }

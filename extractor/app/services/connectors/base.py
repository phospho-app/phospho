class BaseConnector:
    def __init__(self):
        pass

    async def register(self, *args, **kwargs):
        pass

    async def _dump(self):
        pass

    async def pull(self, project_id: str):
        pass

    async def push(
        self,
        org_id: str,
        current_usage: int,
        max_usage: int,
    ):
        pass

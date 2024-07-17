class BaseConnector:
    project_id: str

    def __init__(
        self,
        project_id: str,
    ):
        self.project_id = project_id

    async def register(self, *args, **kwargs):
        raise NotImplementedError

    async def _dump(self):
        raise NotImplementedError

    async def pull(self, project_id: str):
        raise NotImplementedError

    async def push(
        self,
        org_id: str,
        current_usage: int,
        max_usage: int,
    ):
        raise NotImplementedError

    async def sync(self, *args, **kwargs):
        raise NotImplementedError

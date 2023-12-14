class Collection:
    """
    A base class for representing objects of a particular type on the server.
    """

    def __init__(self, client) -> None:
        from phospho.client import Client

        self._client: Client = client

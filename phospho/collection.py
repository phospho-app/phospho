from phospho.client import Client


class Collection:
    """
    A base class for representing objects of a particular type on the server.
    """

    def __init__(self, client: Client) -> None:
        self._client: Client = client

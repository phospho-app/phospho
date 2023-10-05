class Collection:
    """
    A base class for representing objects of a particular type on the server.
    """

    def __init__(self, client) -> None:
        self._client = client

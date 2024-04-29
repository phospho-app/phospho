from pydantic import BaseModel


class ModelsResponse(BaseModel):
    models: list  # List of models objects

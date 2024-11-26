def format_model_id_for_hf(model_id: str) -> str:
    """
    We replace the ":" character with a "-" character in the model_id to match the HuggingFace model hub format.
    """
    return model_id.replace(":", "-")

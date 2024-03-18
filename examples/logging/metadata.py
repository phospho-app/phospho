import phospho
import openai

phospho.init()

# You can log more stuff than just input and output
phospho.log(
    input="input",
    # Output logging is optional and can be set to None
    output=None,
    # Any other additional field will be logged
    metadata={"some additonal metadata": "hello"},
    any_other_name="some_value",
    # Fields that aren't json serializable will be ignored and will raise a warning
    invalid_field=lambda x: x,
)

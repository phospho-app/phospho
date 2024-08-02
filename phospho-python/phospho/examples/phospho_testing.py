import os
import phospho

phospho_test = phospho.PhosphoTest(base_url="http://localhost:8000/v2")

os.environ["MISTRAL_API_KEY"] = "your-api-key"
model = "mistral-small"
client = phospho.lab.get_sync_client("mistral")


@phospho_test.test()
def test_simple():
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an helpful assistant"},
            {"role": "user", "content": "What's bigger: 3.11 or 3.9 ?"},
        ],
    )
    response_text = response.choices[0].message.content
    # Use phospho.log to send the data to phospho for analysis
    phospho.log(
        input="What's bigger: 3.11 or 3.9 ?",
        output=response_text,
        version_id=phospho_test.version_id,
    )


@phospho_test.test(
    source_loader="backtest",  # Load data from logged phospho data
    source_loader_params={"sample_size": 3},
)
def test_backtest(message: phospho.lab.Message) -> str | None:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an helpful assistant"},
            {"role": message.role, "content": message.content},
        ],
    )
    return response.choices[0].message.content

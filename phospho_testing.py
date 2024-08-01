import phospho

phospho_test = phospho.PhosphoTest()

client = phospho.lab.get_sync_client("mistral")


@phospho_test.test()
def test_simple():
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
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
    source_loader_params={"sample_size": 10},
)
def test_backtest(message: str) -> str | None:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an helpful assistant"},
            {"role": "user", "content": message},
        ],
    )
    return response.choices[0].message.content

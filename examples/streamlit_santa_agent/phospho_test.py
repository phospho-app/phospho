"""
This is an example of how to backtest an agent with phospho

1. Setup the API key and project id as environment variables
2. Run the script

```bash
export PHOSPHO_API_KEY=your_api_key
export PHOSPHO_PROJECT_ID=your_project_id
python phospho_test.py
```
"""
import phospho

# This is the agent to test
from backend import SantaClausAgent

phospho.config.BASE_URL = "http://localhost:8000/v0"
phospho_test = phospho.PhosphoTest()


@phospho_test.test(
    source_loader="backtest",
    source_loader_params={"sample_size": 5},
    metrics=["compare"],
)
def test_santa(**inputs):
    santa_claus_agent = SantaClausAgent()
    return santa_claus_agent.answer(**inputs)


@phospho_test.test(
    source_loader="dataset",
    source_loader_params={"path": "golden_dataset.xlsx"},
    metrics=["evaluate"],
)
def test_santa_dataset(input):
    santa_claus_agent = SantaClausAgent()
    return santa_claus_agent.answer(messages=[{"role": "user", "content": input}])


phospho_test.run(executor_type="parallel")

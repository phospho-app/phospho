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
from typing import Dict, List

import phospho

# This is the agent to test
from backend import SantaClausAgent

# phospho.config.BASE_URL = "http://localhost:8000/v0"
phospho_test = phospho.PhosphoTest()


@phospho_test.test(
    source_loader="backtest",  # Load data from logged phospho data
    source_loader_params={"sample_size": 10},
    metrics=[
        "evaluate",  # Evaluate number of successes and failures
        "compare",  # Compare the old and new outputs
    ],
)
def test_santa(messages: List[Dict[str, str]]):
    santa_claus_agent = SantaClausAgent()
    return santa_claus_agent.answer(messages)


@phospho_test.test(
    source_loader="dataset",
    source_loader_params={
        "path": "golden_dataset.xlsx",  # Path to a local file
        "test_n_times": 2,  # Number of times to test the agent on the dataset
    },
    metrics=[
        "evaluate",
        "compare",
    ],
)
def test_santa_dataset(
    input: str,  # The parameters names must match the column name in the dataset
):
    santa_claus_agent = SantaClausAgent()
    return santa_claus_agent.answer(messages=[{"role": "user", "content": input}])


phospho_test.run(executor_type="parallel")

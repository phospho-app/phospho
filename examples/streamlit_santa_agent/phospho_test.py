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
phospho_test = phospho.PhosphoTest(executor_type="parallel", sample_size=5)


@phospho_test.test
def test_santa(**inputs):
    santa_claus_agent = SantaClausAgent()
    return santa_claus_agent.answer(**inputs)


phospho_test.run()

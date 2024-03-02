# phospho: Product Analytics platform for LLM apps

<div align="center">
<img src="./platform/public/image/phospho-banner.png" alt="phospho logo">
<a href="https://www.npmjs.com/package/phospho"><img src="https://img.shields.io/npm/v/phospho?style=flat-square&label=npm+phospho" alt="phospho npm package"></a>
<a href="https://pypi.python.org/pypi/phospho"><img src="https://img.shields.io/pypi/v/phospho?style=flat-square&label=pypi+phospho" alt="phospho Python package on PyPi"></a>
<a href="https://www.ycombinator.com/companies/phospho"><img src="https://img.shields.io/badge/Y%20Combinator-W24-orange?style=flat-square" alt="Y Combinator W24"></a>
<a href="https://discord.gg/MXqBJ9pBsx"><img alt="Discord" src="https://img.shields.io/discord/1106594252043071509"></a>
</div>

Phospho is the product analytics platform for LLM apps. Track user interactions to detect issues and extract insights. Gather user feedback and measure success. Iterate on your app to create the best conversational experience for your users.

Ship your LLM app with in production with confidence, and iterate on it with insights from your users.

Support us by starring this repo! ⭐

## Key Features

- Flexible logging
- Automatic evaluation
- Insights extraction
- Data visualization
- Collaboration

![The phospho lab is the core analytics component of phospho](./phospho_diagram.png)

## Demo

https://github.com/phospho-app/phospho/assets/78322686/fb1379bf-32f1-492e-be86-d29879056dc3

## Quickstart: Discover the phospho lab

The phospho lab is the core analytics component of phospho. The phospho lab helps you run batched evaluations and event detections on your messages.

Install the phospho lab:

```
pip install "phospho[lab]"
```

We will run a simple Event detection job that use OpenAI to read a message and figure out whether an Event happened or not.

```bash
export OPENAI_API_KEY=your_openai_api_key
```

Phospho helps you define a bunch of jobs to efficiently run in a workload on users messages.

```python
from phospho import lab

# A workload is a set of jobs to run on messages
# A job is a Python function that leverages LLM and ML models to extract insights from text
workload = lab.Workload()
workload.add_job(
   lab.Job(
         id="question_answering",
         job_function=lab.job_library.event_detection,
         config=lab.EventConfig(
            event_name="question_answering",
            event_description="The user asks a question to the assistant",
         ),
   )
)

# The workload runs the jobs in parallel on all the messages to perform analytics
await workload.async_run(
   messages=[
      lab.Message(
            id="my_message_id",
            role="User",
            content="What is the weather today in Paris?",
         )
   ],
)

message_results = workload.results["my_message_id"]
print(f"The event question_answering was detected: {message_results['question_answering'].value}")
```

You get:

```
The event question_answering was detected: True
```

This event detection pipeline can then be linked to other bricks through webhooks or used to notice patterns in the user data.

You can use other jobs from the library or create your own jobs to run on your messages.

## Access the hosted version

To manage the phospho lab evaluations on a collaborative platform, the easiest way is to register to the hosted version.

1. Create a [phospho account](https://phospho.ai)
2. Install a phospho client: `pip install phospho` or `npm i phospho`
3. Create environment variables for `PHOSPHO_API_KEY` and `PHOSPHO_PROJECT_ID`
4. Initialize phospho: `phospho.init()`
5. Log to phospho with `phospho.log(input="question", output="answer")`

[Follow this guide to get started.](https://docs.phospho.ai/getting-started)

### Self deploy

This repository contains the implementation of the platform frontend, the API backend, and the insights extraction pipeline.

- `phospho-python`: Python client with analytics engine
- `extractor`: FastAPI analytics service wrapping the analytics engine
- `backend`: FastAPI backend
- `platform`: NextJS frontend
- `internal-tools`: Platform management tools

1. Clone the repo:

```bash
git clone git@github.com:phospho-app/monorepo.git
```

2. Register to the core external services:
   - OpenAI (or another OpenAI-compatible model provider)
   - Cohere
   - MongoDB Atlas (Alternative: self host a MongoDB)
3. (Optional) Extend the platform capabilities by registering to additional services:

   - Resend (emails)
   - Sentry (performance analytics)
   - Propelauth (authentication)
   - Stripe (payment)

4. Follow the deployment instructions in backend/README.md and platform/README.md

5. Enjoy !

## Licence

This project is licensed under the Apache 2.0 License - see the [LICENSE file](./LICENCE) for details

## Related projects

- [phospho Javascript client](https://github.com/phospho-app/phosphojs)
- [phospho UI React components](https://github.com/phospho-app/phospho-ui-react)
- [phospho fastassert constrained inference](https://github.com/phospho-app/fastassert)

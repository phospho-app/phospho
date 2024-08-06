# phospho: Text Analytics Platform for LLM Apps

<div align="center">
<img src="./platform/public/image/phospho-banner.png" alt="phospho logo">
<a href="https://www.npmjs.com/package/phospho"><img src="https://img.shields.io/npm/v/phospho?style=flat-square&label=npm+phospho" alt="phospho npm package"></a>
<a href="https://pypi.python.org/pypi/phospho"><img src="https://img.shields.io/pypi/v/phospho?style=flat-square&label=pypi+phospho" alt="phospho Python package on PyPi"></a>
<a href="https://www.ycombinator.com/companies/phospho"><img src="https://img.shields.io/badge/Y%20Combinator-W24-orange?style=flat-square" alt="Y Combinator W24"></a>
<a href="https://pypi.org/project/phospho/" target="_blank"><img src="https://img.shields.io/pypi/dm/phospho"></a>
<a href="https://discord.gg/m8wzBGQA55" target="_blank"><img src="https://img.shields.io/badge/Join%20our%20community-Discord-blue"></a>
</div>

Phospho is the text analytics platform for LLM apps. Detect issues and extract insights from text messages of your users or your app. Gather user feedback and measure success. Iterate on your app to create the best conversational experience for your users.

Ship your LLM app in production with confidence, and iterate on it with insights from your users.

Learn more in the full [documentation](https://docs.phospho.ai/welcome).

## Key Features

- Flexible logging
- Automatic evaluation
- Insights extraction
- Data visualization
- Collaboration

<div align="center">
<img src="./phospho_diagram.png" alt="phospho diagram" width=450>
</div>

## Demo

https://github.com/phospho-app/phospho/assets/66426745/5422d3b5-4f78-4445-be72-ff51eba26efb

## Quickstart: Discover the phospho lab in pure python

The phospho lab is the core analytics component of phospho. The phospho lab helps you run batched evaluations and event detections on your messages.

```bash
pip install "phospho[lab]"
```

Follow the quickstart [here](https://docs.phospho.ai/local/quickstart).

## Self deploy

This repository contains the implementation of the platform frontend, the API backend, and the insights extraction pipeline.

- `phospho-python`: Python client with analytics engine
- `extractor`: FastAPI analytics service wrapping the analytics engine
- `backend`: FastAPI backend
- `platform`: NextJS frontend
- `internal-tools`: Platform management tools

### Prerequisites

Ensure you have the following installed:

- Docker
- Docker Compose

### 60 seconds deploy

1. Clone the repo:

```bash
git clone git@github.com:phospho-app/phospho.git && cd phospho
```

2. Register to the core external services:

- [OpenAI](https://platform.openai.com) if you do not want to use Ollama
- [Propelauth](https://www.propelauth.com) (the free tier is enough for testing purposes)

3. Create a copy of the `.env.example` file as a `.env.docker` files

```bash
cp .env.example .env.docker
```

4. Complete the `.env.docker` file with secret variables

```bash
nano .env.docker # or emacs or vscode or vim
```

By default, phospho analytics pipeline use OpenAI as their main LLM provider.

To use Ollama, set `OVERRIDE_WITH_OLLAMA_MODEL=mistral` (or any model) in `.env.docker`. In this case, the`OPENAI_API_KEY` variable is not used. You do need to have an Ollama instance set up and running.

5. Launch the project

```bash
docker-compose up
```

6. Start using phospho

Go the platform at `http://localhost:3000` to grab your project id and api key.
Log your first message :

```bash
export PHOSPHO_PROJECT_ID="your_project_id"
export PHOSPHO_API_KEY="your_api_key"
curl -X POST "http://localhost:80/v2/log/$PHOSPHO_PROJECT_ID" -H "Authorization: Bearer $PHOSPHO_API_KEY" -H "Content-Type: application/json" -d '{"batched_log_events": [{"input": "Hi, I just logged my first task to phospho!","output": "Congrats! Keep pushing!"}]}'
```

Don't forget to specify your backend url when you use the client libraries in your app. By default it's `http://localhost:80`

## Access the hosted version

To manage the phospho lab evaluations on a collaborative platform, the easiest way is to register to the hosted version.

1. Create a [phospho account](https://phospho.ai)
2. Install a phospho client: `pip install phospho` or `npm i phospho`
3. Create environment variables for `PHOSPHO_API_KEY` and `PHOSPHO_PROJECT_ID`
4. Initialize phospho: `phospho.init()`
5. Log to phospho with `phospho.log(input="question", output="answer")`

[Follow this guide to get started.](https://docs.phospho.ai/getting-started)

## Licence

This project is licensed under the Apache 2.0 License - see the [LICENSE file](./LICENCE) for details

## Related projects

- [phospho Javascript client](https://github.com/phospho-app/phosphojs)
- [phospho UI React components](https://github.com/phospho-app/phospho-ui-react)
- [phospho fastassert constrained inference](https://github.com/phospho-app/fastassert)

## Contributing

We welcome contributions from the community. Please refer to our [contributing guidelines](./CONTRIBUTE.md) for more information.

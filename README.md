# The LLM app backoffice for busy builders

<div align="center">
<img src="./platform/public/image/phospho-banner.png" alt="phospho logo">
<a href="https://www.npmjs.com/package/phospho"><img src="https://img.shields.io/npm/v/phospho?style=flat-square&label=npm+phospho" alt="phospho npm package"></a>
<a href="https://pypi.python.org/pypi/phospho"><img src="https://img.shields.io/pypi/v/phospho?style=flat-square&label=pypi+phospho" alt="phospho Python package on PyPi"></a>
<a href="https://www.ycombinator.com/companies/phospho"><img src="https://img.shields.io/badge/Y%20Combinator-W24-orange?style=flat-square" alt="Y Combinator W24"></a>
<a href="https://pypi.org/project/phospho/" target="_blank"><img src="https://img.shields.io/pypi/dm/phospho"></a>
</div>

🧪 **phospho** is the **backoffice for your LLM app.**

Detect issues and extract insights from your users' text messages.

Gather feedback and measure success. Create the best conversational experience for your users.
Analyze logs effortlessly and finally make sense of all your data.

Learn more in the [documentation](https://docs.phospho.ai/welcome).

<div align="center">
<img src="./clustering-demo.gif" alt="phospho platform">
</div>

## Demo 🧪

https://github.com/phospho-app/phospho/assets/66426745/5422d3b5-4f78-4445-be72-ff51eba26efb

## Key Features 🚀

- **Clustering**: Group similar conversations and identify patterns
- **A/B Testing**: Compare different versions of your LLM app
- **Data Labeling**: Efficiently categorize and annotate your data
- **User Analytics**: Gain insights into user behavior and preferences
- **Integration**: Sync data with LangSmith/Langfuse, Argilla, PowerBI
- **Data Visualization**: Powerful tools to understand your data
- **Multi-user Experience**: Collaborate with your team seamlessly

## Quick start: How to setup phospho SaaS?

Quickly import, analyze and label data on the [phospho platform](https://phospho.ai).

1. Create an [account](https://phospho.ai)
2. Install our SDK:

- Python: `pip install phospho`
- JavaScript: `npm i phospho`

3. Set environment variables ( you can find these on your phospho account )

- `PHOSPHO_API_KEY`
- `PHOSPHO_PROJECT_ID`

4. Initialize phospho: `phospho.init()`
5. Start logging to phospho with `phospho.log(input="question", output="answer")`

[Follow this guide to get started.](https://docs.phospho.ai/getting-started)

**Note:**

- You can also import data directly through a CSV or Excel directly on the platform
- If you use the python version, you might want to disable auto-logging with `phospho.init(auto_log=False)`

## Deploy with docker compose

Create a `.env.docker` using [this guide](./DeploymentGuide.md). Then, run:

```bash
docker compose up
```

Go to `localhost:3000` to see the platform frontend. The backend documentation is available at `localhost:8000/v3/docs`.

## Development guide

### Contributing

We welcome contributions from the community. Please refer to our [contributing guidelines](./CONTRIBUTE.md) for more information.

### Running locally

This project uses Python3.11+ and [NextJS](https://nextjs.org/docs). To work on it locally, create a python virtual environment.

Make sure you have properly added `.env` files in `ai-hub`, `extractor`, `backend`, `platform`.

Then, the quickest way to get started is to use the makefile.

```bash
python -m venv .venv
make install
# Launch everything
make up
```

Go to `localhost:3000` to see the platform frontend. The backend documentations are available at `localhost:8000/api/docs`, `localhost:8000/v2/docs` and `localhost:8000/v3/docs`.

To stop everything, run:

```bash
make stop
```

## Related projects

- [AI chat bubble with Mistral](https://github.com/phospho-app/ai-chat-bubble) - custom AI assistant connected to your knowledge
- [chatbot template streamlit OpenAI](https://github.com/phospho-app/template-chatbot-streamlit-openai)
- [phospho Javascript client](https://github.com/phospho-app/phosphojs)
- [phospho UI React components for user feedback](https://github.com/phospho-app/phospho-ui-react)

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE file](./LICENCE) for details

## About us

We are a team of passionate AI builders, feel free to reach out [here](mailto:contact@phospho.ai?subject=Hey%20baguettes). _With love and baguettes from Paris, the phospho team 🥖💚_

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=phospho-app/phospho&type=Date)](https://star-history.com/#phospho-app/phospho&Date)

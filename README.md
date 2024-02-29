# phospho: Product Analytics platform for LLM apps

<div align="center">
<img src="./platform/public/image/phospho-banner.png" alt="phospho logo">
<a href="https://www.npmjs.com/package/phospho"><img src="https://img.shields.io/npm/v/phospho?style=flat-square&label=npm+phospho" alt="phospho npm package"></a>
<a href="https://pypi.python.org/pypi/phospho"><img src="https://img.shields.io/pypi/v/phospho?style=flat-square&label=pypi+phospho" alt="phospho Python package on PyPi"></a>
<a href="https://www.ycombinator.com/companies/phospho"><img src="https://img.shields.io/badge/Y%20Combinator-W24-orange?style=flat-square" alt="Y Combinator W24"></a>
<a href="https://discord.gg/MXqBJ9pBsx"><img alt="Discord" src="https://img.shields.io/discord/1106594252043071509"></a>
</div>

Phospho is the product analytics platform for LLM apps. Track user interactions to detect issues and extract insights. Gather user feedback and measure success. Iterate on your app to create the best conversational experience for your users.

## Key Features

- Flexible logging
- Automatic evaluation
- Insights extraction
- Data visualization
- Collaboration

## Demo

https://github.com/phospho-app/monorepo/assets/58109554/efad0411-5647-42e8-81d3-73971ac6de7f

## Get started

### Hosted version

The easiest way to get started with phospho is to use the hosted cloud version of the app:

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

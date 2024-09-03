# phospho: the LLM app backoffice for busy builders

<div align="center">
<img src="./platform/public/image/phospho-banner.png" alt="phospho logo">
<a href="https://www.npmjs.com/package/phospho"><img src="https://img.shields.io/npm/v/phospho?style=flat-square&label=npm+phospho" alt="phospho npm package"></a>
<a href="https://pypi.python.org/pypi/phospho"><img src="https://img.shields.io/pypi/v/phospho?style=flat-square&label=pypi+phospho" alt="phospho Python package on PyPi"></a>
<a href="https://www.ycombinator.com/companies/phospho"><img src="https://img.shields.io/badge/Y%20Combinator-W24-orange?style=flat-square" alt="Y Combinator W24"></a>
<a href="https://pypi.org/project/phospho/" target="_blank"><img src="https://img.shields.io/pypi/dm/phospho"></a>
<a href="https://discord.gg/m8wzBGQA55" target="_blank"><img src="https://img.shields.io/badge/Join%20our%20community-Discord-blue"></a>
</div>

Phospho is the backoffice for your LLM apps. Detect issues and extract insights from your app's text messages. Gather user feedback and measure success. Create the best conversational experience for your users.

Ship your LLM app in production with confidence, and focus on user insights to iterate.

Learn more in the full [documentation](https://docs.phospho.ai/welcome).

## Key Features

- **Clustering**: Group similar conversations and identify patterns
- **A/B Testing**: Compare different versions of your LLM app
- **Data Labeling**: Efficiently categorize and annotate your data
- **User Analytics**: Gain insights into user behavior and preferences
- **Integration**: Sync data with LangSmith/Langfuse, Argilla, PowerBI
- **Data Visualization**: Powerful tools to understand your data
- **Multi-user Experience**: Collaborate with your team seamlessly

## Demo

https://github.com/phospho-app/phospho/assets/66426745/5422d3b5-4f78-4445-be72-ff51eba26efb

## Quickstart: Discover the phospho lab in pure python

phospho lab is the core analytics component of phospho, it let's you detect events defined in natural language in your data.

Leverage your data by batching the event dectection process with phospho lab.

```bash
pip install "phospho[lab]"
```

Follow the quickstart [here](https://docs.phospho.ai/local/quickstart).

## Access the hosted version

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

## Use phospho as a white label

Want to get the hosted version of phospho as a white label platform?

Contact us [here](mailto:contact@phospho.ai?subject=[GitHub]%20phospho%20white%label) to get your own white label backoffice for your llm apps.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE file](./LICENCE) for details

## Related projects

- [phospho Javascript client](https://github.com/phospho-app/phosphojs)
- [phospho UI React components](https://github.com/phospho-app/phospho-ui-react)
- [phospho fastassert constrained inference](https://github.com/phospho-app/fastassert)

## Contributing

We welcome contributions from the community. Please refer to our [contributing guidelines](./CONTRIBUTE.md) for more information.

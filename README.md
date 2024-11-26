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

## Use phospho as a white label solution

Want to get the hosted version of phospho as a white label platform?

Contact us [here](mailto:contact@phospho.ai?subject=[GitHub]%20phospho%20white%label) to get your own white label backoffice for your llm apps.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE file](./LICENCE) for details

## Related projects

- [chatbot template streamlit OpenAI](https://github.com/phospho-app/template-chatbot-streamlit-openai)
- [phospho Javascript client](https://github.com/phospho-app/phosphojs)
- [phospho UI React components for user feedback](https://github.com/phospho-app/phospho-ui-react)

## Contributing

We welcome contributions from the community. Please refer to our [contributing guidelines](./CONTRIBUTE.md) for more information.

## About us

We are a team of passionate AI builders, feel free to reach out [here](mailto:contact@phospho.ai?subject=Hey%20baguettes)

_With love and baguettes from Paris, the phospho team 🥖💚_

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=phospho-app/phospho&type=Date)](https://star-history.com/#phospho-app/phospho&Date)

## Installation

### Requirements

This project uses Poetry and a version of Python above 3.11

1. **Create a Virtual Environment**  
   Run the following command to create a virtual environment:

```bash
# 1 - enter backend
cd backend
# 2 first option - create a virtual environment
conda create -n phospho-env python=3.11
# 2 second option - create a virtual environment
python -m venv
```

2. **Install and Run the Phospho Platform**
   To set up and run the Phospho platform locally, follow these steps:

   - **Frontend**: Access the `platform`folder through the terminal. Refer to the instructions in the README file located in the `platform` folder.
   - **Backend**: Access the `platform`folder through the terminal.Refer to the README file located in the `backend` folder.
   - **AI Hub**: Access the `ai-hub` folder through the terminal. Follow the instructions in the README file located in the `ai-hub` folder.

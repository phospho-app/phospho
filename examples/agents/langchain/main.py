"""
This is an example of how to integrate phospho with a simple RAG langchain agent.

1. Set the following environment variables:

```
export PHOSPHO_API_KEY=...
export PHOSPHO_PROJECT_ID=...
export OPENAI_API_KEY=...
```

2. Start the langchain agent

```
pip install -r requirements.txt
python main.py
```

This will start a simple chatbot that can answer questions based on a context.
"""

from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

vectorstore = FAISS.from_texts(
    [
        "Phospho is the LLM analytics platform",
        "Paris is the capital of Fashion (sorry not sorry London)",
        "The Concorde had a maximum cruising speed of 2,179 km (1,354 miles) per hour, or Mach 2.04 (more than twice the speed of sound), allowing the aircraft to reduce the flight time between London and New York to about three hours.",
    ],
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()
template = """Answer the question based only on the following context:
{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
model = ChatOpenAI()

retrieval_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)


# To integrate with Phospho, add the following callback handler
# https://python.langchain.com/docs/modules/callbacks/

from phospho.integrations import PhosphoLangchainCallbackHandler

while True:
    text = input("Enter a question: ")
    response = retrieval_chain.invoke(
        text, config={"callbacks": [PhosphoLangchainCallbackHandler()]}
    )
    print(response)

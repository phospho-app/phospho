from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# To integrate with Phospho, add the following callback handler
# https://python.langchain.com/docs/modules/callbacks/

from phospho.integrations import PhosphoLangchainCallbackHandler

# Langchain agent code

vectorstore = DocArrayInMemorySearch.from_texts(
    [
        "Phospho is an LLM analytics platform to help you improve your LLM apps",
        "Paris is the capital of fashion (sorry not sorry London!)",
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
output_parser = StrOutputParser()

setup_and_retrieval = RunnableParallel(
    {"context": retriever, "question": RunnablePassthrough()}
)

chain = setup_and_retrieval | prompt | model | output_parser

# Add the callback handler when invoking the chain to log tasks to phospho
phospho_log = PhosphoLangchainCallbackHandler()

while True:
    query = input("Enter a question: ")
    response = chain.invoke(query, config={"callbacks": [phospho_log]})
    print(response)

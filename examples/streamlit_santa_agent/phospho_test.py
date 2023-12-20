"""
This is an example of how to backtest an agent with phospho
"""
import phospho
import streamlit as st

# This is the agent to test
from backend import SantaClausAgent

phospho_test = phospho.PhosphoTest(
    api_key=st.secrets["PHOSPHO_API_KEY"],
    project_id=st.secrets["PHOSPHO_PROJECT_ID"],
)


@phospho_test.test
def test_santa():
    santa_claus_agent = SantaClausAgent()
    new_output = santa_claus_agent.answer(**input)


phospho_test.run()

# pages/agent_test.py

import streamlit as st
import pandas as pd
from bq_agent import query_bigquery_agent # Import the function

st.title("🏈 Fantasy Football Data Analyst")
st.markdown("""
Ask natural language questions about your BigQuery fantasy football data!
""")

user_question = st.text_input("Ask a question about your fantasy football data:", "")

if user_question:
    with st.spinner("Thinking..."):
        response = query_bigquery_agent(user_question)
        st.subheader("Answer:")
        
        # This parsing logic will depend on the LLM's output.
        # It's a simple heuristic for markdown tables.
        if isinstance(response, str) and response.strip().startswith("|") and "|---|---" in response:
            try:
                lines = response.strip().split('\n')
                header = [col.strip() for col in lines[0].strip('|').split('|')]
                data = [list(map(str.strip, row.strip('|').split('|'))) for row in lines[2:]]
                df = pd.DataFrame(data, columns=header)
                st.dataframe(df)
            except Exception:
                st.write(response)
        else:
            st.write(response)

st.markdown("---")
st.caption("Powered by LangChain, Google Gemini, and BigQuery.")
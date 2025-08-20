# bq_agent.py

import os
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import AgentExecutor
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType
from google.cloud import bigquery
import pandas as pd
import streamlit as st

# --- Configuration ---
PROJECT_ID = st.secrets["google_credentials"]["project_id"]
DATASET_NAME = "dbt_production"
TABLE_NAME = "fct_results" # Your view name

# --- Initialize BigQuery Client (for schema and direct queries) ---
try:
    credentials_dict = dict(st.secrets["google_credentials"])
    client = bigquery.Client.from_service_account_info(credentials_dict, project=PROJECT_ID)
except Exception as e:
    st.error(f"Error initializing BigQuery client with st.secrets: {e}")
    st.error("Please ensure your .streamlit/secrets.toml is correctly configured.")
    st.stop()

def get_bigquery_uri_for_sqlalchemy():
    return f"bigquery://{PROJECT_ID}/{DATASET_NAME}"

def create_sql_agent_for_bigquery():
    db_uri_for_sqlalchemy = get_bigquery_uri_for_sqlalchemy()
    secrets_credentials_info = dict(st.secrets["google_credentials"])

    db = SQLDatabase.from_uri(
        db_uri_for_sqlalchemy,
        include_tables=[TABLE_NAME],
        view_support=True,
        engine_args={
            "credentials_info": secrets_credentials_info
        }
    )

    gemini_api_key = st.secrets["gemini"]["api_key"]
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1, google_api_key=gemini_api_key)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    agent_executor = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True
    )
    return agent_executor

def query_bigquery_agent(question: str) -> str:
    agent = create_sql_agent_for_bigquery()
    try:
        response = agent.invoke({"input": question})
        return response.get("output", response.get("answer", "No specific answer found."))
    except Exception as e:
        return f"An error occurred: {e}"
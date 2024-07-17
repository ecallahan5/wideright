import streamlit as st
import requests
import global_vars
import config
import datetime
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery
import os

site_token = config.key

# Get the list of teams
# @st.cache_data(show_spinner="Getting Teams...", ttl=datetime.timedelta(days=1))
def get_teams():
    r = requests.get(url = global_vars.franchises_URL, headers={'Authorization': 'Bearer ' + site_token }) 
    franchises = r.json()
    return franchises

# Get the list of players
@st.cache_data(show_spinner="Getting Players...", ttl=datetime.timedelta(days=1))
def get_players():
    r = requests.get(url = global_vars.players_URL, headers={'Authorization': 'Bearer ' + site_token }) 
    players = r.json()
    return players

# Get the list of players from Wide Right server
@st.cache_data(show_spinner="Getting Players...", ttl=datetime.timedelta(days=1))
def get_players_wr():
    r = requests.get(url = global_vars.players_URL_wr, headers={'Authorization': 'Bearer ' + site_token }) 
    players = r.json()
    return players

@st.cache_data(show_spinner="Getting Schedules...", ttl=datetime.timedelta(days=1))
def get_schedule():
    r = requests.get(url = global_vars.schedule_URL, headers={'Authorization': 'Bearer ' + site_token })
    schedule = r.json()
    return schedule

@st.cache_data(show_spinner="Getting Rosters...", ttl=datetime.timedelta(days=1))
def get_rosters():
    r = requests.get(url = global_vars.rosters_URL, headers={'Authorization': 'Bearer ' + site_token })
    rosters = r.json()
    return rosters

@st.cache_data(show_spinner="Getting Probabilites...", ttl=datetime.timedelta(days=1))
def get_probs():
    r = requests.get(url = global_vars.probs_URL, headers={'Authorization': 'Bearer ' + site_token , 'Accept': 'application/json'})
    probs = r.json()[0]
    probs_df = pd.DataFrame(probs)
    return probs_df

@st.cache_data(show_spinner="Getting Standings...", ttl=datetime.timedelta(days=1))
def get_standings():
    r = requests.get(url = global_vars.standings_URL, headers={'Authorization': 'Bearer ' + site_token , 'Accept': 'application/json'})
    data = r.json()
    vals = list(data.values())
    exclude = ["id", "updated_at"]
    df = pd.DataFrame.from_records(vals[0], exclude = exclude)
    standings = df.sort_values(by = ["franchise_division", "wins"], ascending= [True, False])
    cols_to_float = ['wins', 'losses', 'division_wins', 'division_losses', 'after_week']
    for col in cols_to_float:
        standings[col] = standings[col].apply(lambda x: int(x))
    standings["current_wk"] = standings["after_week"] + 1
    latest_wk = (max(standings["after_week"]))
    return standings, latest_wk

@st.cache_data(show_spinner="Getting Dates...", ttl=datetime.timedelta(days=7))
def get_dates():
    r = requests.get(url = global_vars.calendar_URL, headers={'Authorization': 'Bearer ' + site_token})
    dates = r.json()["calendar"]["event"]
    dates_df = pd.DataFrame(dates)
    return dates_df

@st.cache_data(show_spinner="Getting Extensions...", ttl=datetime.timedelta(days=7))
def get_extensions():
    r = requests.get(url = global_vars.extensions_url, headers={'Authorization': 'Bearer ' + site_token})
    extensions = r.json()
    extensions_df = pd.DataFrame(extensions)
    return extensions_df

# Accessing the secret from environment variables
credentials_info = json.loads(os.getenv("GCP_SERVICE_ACCOUNT"))

# Create credentials object
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Create BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials_info["project_id"])




# # Create API client.
# credentials = service_account.Credentials.from_service_account_info(
#     secrets["GCP_CREDENTIALS"]
# )
# # Create BigQuery client
# client = bigquery.Client(credentials=credentials, project=st.secrets["gcp_service_account"]["project_id"])

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(show_spinner="Trying to figure out how to beat Kevin...", ttl=datetime.timedelta(days=1))
def bq_query(query):
    query_job = client.query(query)
    rows_raw = query_job.result()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    rows = [dict(row) for row in rows_raw]
    return rows

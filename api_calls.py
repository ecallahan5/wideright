import streamlit as st
import requests
import global_vars
import config
import datetime

site_token = config.key

# Get the list of teams
@st.cache_data(show_spinner="Getting Teams...", ttl=datetime.timedelta(days=1))
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

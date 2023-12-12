import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import config
import global_vars
import api_calls

st.set_page_config(layout="wide")
st.title("Playoff Seeding")
st.subheader("Championship Bracket", divider=True)

seeds = pd.DataFrame({
     'Seed': [1,2,3,4,5,6],
     'Team': ["The Van Buren Boys", "Uncaught Exceptions", "Brooklyn Big Blue", "Maize 'N Blue", "Moneyballers", "The Gurley Tates"]
     })
st.dataframe(seeds, hide_index=True, use_container_width = True)

st.subheader("Consolation Bracket", divider=True)
seeds = pd.DataFrame({
     'Seed': [1,2,3,4,5,6],
     'Team': ["You Carr'd Be Kidding", "Cromarties Bastards", "Muthah Tucker", "Shoot'em into the sun", "Hidden Talents", "Hurricane"]
     })
st.dataframe(seeds, hide_index=True, use_container_width = True)

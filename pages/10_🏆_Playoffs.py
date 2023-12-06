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

seeds = pd.DataFrame({
     'Seed': [1,2,3,4,5,6],
     'Team': ["", "", "", "", "", ""]
     })
st.dataframe(seeds, hide_index=True, use_container_width = True)

st.subheader("Eliminated from Championship Bracket", divider=True)
st.write("Hurricane")
st.write("Hidden Talents")
st.write("Shoot'em Into the Sun")
st.write("Muthah Tucker")
st.write("Cromarties Bastards")

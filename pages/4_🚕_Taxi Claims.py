import pandas as pd
import streamlit as st
import requests
import json
import config
import functions
import global_vars
from datetime import datetime, timedelta

site_token = config.key

st.set_page_config(layout="wide")

current_wk = functions.bq_query("SELECT current_week FROM `mfl-374514.dbt_production.dim_current_week`")[0]["current_week"]

st.title("Taxi Claims for Week "+str(current_wk) )
st.divider()

# Import Claimables
if current_wk >= 8:
    claimables = functions.bq_query("SELECT * FROM `mfl-374514.dbt_production.taxi_claimables`")
else:
    claimables = functions.bq_query("SELECT * FROM `mfl-374514.dbt_production.taxi_claimables where ffp_flag = 0`")
claimables_df = pd.DataFrame(claimables)

# #Table style
st.markdown(global_vars.hide_table_row_index, unsafe_allow_html=True)

# #Table style
st.markdown(global_vars.hide_table_row_index, unsafe_allow_html=True)
keep_cols = ["player_name", 'position', "ytd_pts", "current_team_name", "ffp_flag", "comp_pick"]


with st.chat_message("Norwood", avatar = global_vars.norwood_avatar):
    st.write("What team are you claming for?")
    team = st.selectbox(
    '', [""] + sorted(claimables_df["claiming_team_name"].unique()))
    if team:
        st.write("Here are the players that " + team + " can claim:" )

        claimables_df = claimables_df.loc[claimables_df["claiming_team_name"] == team][keep_cols].rename \
            ({'player_name' : 'Name', 'position' : 'Position', 'current_team_name' : 'Owner' , 'ytd_pts' : '2024 Pts'}, axis = 1)
        claimables_df['2024 Pts'] = claimables_df['2024 Pts'].map('{:.2f}'.format)
        st.table(claimables_df.iloc[:, :4])

        st.write("Would you like to claim any of these players?")
        claim = st.checkbox("Yes!")
        if claim:
            claiming = st.radio("Who would you like to claim?", claimables_df)
            name = claimables_df.loc[claimables_df["Name"] == claiming]["Name"].values[0]
            owner = claimables_df.loc[claimables_df["Name"] == claiming]["Owner"].values[0]
            comp_pick = int(claimables_df.loc[claimables_df["Name"] == claiming]["comp_pick"].values[0])
            if claimables_df.loc[claimables_df["Name"] == name]["ffp_flag"].values[0] == 1:
                st.warning(name+" is a designated Future Franchise Player (FFP). If you'd like to claim him you must surrender a future pick in Round "+str(comp_pick), icon="⚠️")
            st.write("Would you like to claim " + name + " from " + owner + " ?")
            claim_action = st.button("Claim him!")
            if claim_action:
                webhook_url = 'https://discord.com/api/webhooks/1285395444209418280/YylZOUyFp0rSGfLOEg44zbnMMRfz9Pnq-lJTEKhxNr-a-4FzpJmidAQqMPp9JIws3de0'
                current_time = datetime.now()
                one_week_later = (datetime.now() + timedelta(weeks=1)).strftime("%A, %B %d, %I:%M %p")
                if claimables_df.loc[claimables_df["Name"] == name]["ffp_flag"].values[0] == 1:
                    payload = {"content": "**" + team + "** is submitting a 🚕 claim on **" + name + "** from **" + owner + "**.  This is an FFP claim and carries draft pick compensation. The claim must be resolved by **" + one_week_later + "**."}
                else:
                    payload = {"content": "**" + team + "** is submitting a 🚕 claim on **" + name + "** from **" + owner + "**. The claim must be resolved by **" + one_week_later + "**."}
                r = requests.post(url = webhook_url, data = payload)
                if r: 
                    st.toast("Your claim has been submitted!", icon='🎉')
                    


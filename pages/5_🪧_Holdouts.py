import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import config
import global_vars
from google.oauth2 import service_account
# from gsheetsdb import connect
import gspread
from oauth2client.service_account import ServiceAccountCredentials


site_token = config.key

st.set_page_config(layout="wide")
st.title("Holdouts Voting")
st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

st.subheader("See you in 2024!")

# # Load the Google Sheets credentials
# scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(config.google_credentials, strict=False), scope)

# # Initialize the Google Sheets client
# client = gspread.authorize(creds)

# # # Define the Google Sheet destination URL 
# sheet_url = config.google_sheet_url

# # Get the current rosters
# r = requests.get(url = global_vars.rosters_URL, headers={'Authorization': 'Bearer ' + site_token }) 
# rosters = r.json()
# keep_cols = ["mfl_id", "franchise_name", "salary", "contract_years", "status"]
# rosters_df = pd.DataFrame(rosters)[keep_cols]
# rosters_df['mfl_id'] = rosters_df['mfl_id'].astype(str)

# Get player metadata
# players = api_calls.get_players_wr()
# keep_cols = ["position", "mfl_id", "first_name", "last_name"]
# players_df = pd.DataFrame(players)[keep_cols]
# players_df["mfl_id"] = players_df["mfl_id"].astype(str)

# # Join player dfs
# players_df1 = rosters_df.merge(players_df, how = 'left', left_on = 'mfl_id', right_on = 'id').drop(['id'], axis=1)

# # Filter for Holdout Eligible Players 
# holdouts_df = players_df1.loc[players_df1["mfl_id"].isin(global_vars.holdouts_2023)].sort_values(by=["salary"], ascending = False).drop(['mfl_id', 'status'], axis=1)


# # Get the list of teams
# r = requests.get(url = global_vars.franchises_URL, headers={'Authorization': 'Bearer ' + site_token }) 
# franchises = r.json()
# keep_cols = ["franchise_name"]
# df_franchises = pd.DataFrame(franchises)[keep_cols]

# # Create the Streamlit form
# def create_form():
#     selected_rows = []
#     st.subheader("Who is voting?")
#     team_name = st.selectbox("Team Name", df_franchises)
#     selected_rows.append(team_name)
#     for i in range(5):
#         st.subheader(f"Holdout {i+1}")
#         row_name = st.selectbox(f"Select a Player", [""] + holdouts_df["name"].tolist(), key=f"row_{i}")
#         if row_name != "":
#             selected_row = holdouts_df.loc[holdouts_df["name"] == row_name]["name"].values[0]
#             selected_rows.append(selected_row)

#     submit_button = st.button("Submit")
#     return selected_rows, submit_button

# # Write the form submission to the Google Sheet
# def write_to_google_sheet(submission):
#     sheet = client.open_by_url(sheet_url).sheet1
#     for row in submission:
#         row_without_comma = row.replace(",", "") 
#         sheet.append_row([row_without_comma])

# # Main Streamlit code
# def main():
#     st.title("Holdout Eligible Players")
#     st.dataframe(holdouts_df, use_container_width=True, hide_index=True,      
#         column_config={
#         "name": "Player",    
#         "franchise_name": "Franchise",
#         "position": "Position",
#         "contract_years": "Years Remaining",
#         "salary": st.column_config.NumberColumn(
#             "Salary",
#             format="$%d")
#     },
#         column_order=("name", "position", "salary", "contract_years", "franchise_name") )
#     st.title("Holdouts Ballot")

#     selected_rows, submit_button = create_form()

#     if submit_button:
#         # selected_data = holdouts_df.iloc[selected_rows]
#         # st.write(selected_rows)
#         write_to_google_sheet(selected_rows)
#         st.success("Form submitted successfully!")

# if __name__ == "__main__":
#     main()












import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import config
import global_vars
import functions
# from google.oauth2 import service_account
# from gsheetsdb import connect
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(layout="wide")
st.title("Holdouts Voting")
st.divider()

# Get the holdout list picks 
players = functions.bq_query("SELECT * FROM `mfl-374514.dbt_production.fct_holdout_players`")
players_df = pd.DataFrame(players)
players_df
# picks_df[["year", "round_num"]] = picks_df[["year", "round_num"]].apply(pd.to_numeric)


# Load the Google Sheets credentials
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(config.google_credentials, strict=False), scope)

# Initialize the Google Sheets client
client = gspread.authorize(creds)

# Define the Google Sheet destination URL 
sheet_url = config.holdouts_voting_sheet_url

franchises = functions.bq_query("SELECT name FROM `mfl-374514.dbt_production.fct_franchises`")
franchises_df = pd.DataFrame(franchises)


# Create the Streamlit form
def create_form():
    selected_rows = []
    st.subheader("Who is voting?")
    team_name = st.selectbox("Team Name", franchises_df)
    selected_rows.append(team_name)
    for i in range(5):
        st.subheader(f"Holdout {i+1}")
        row_name = st.selectbox(f"Select a Player", [""] + players_df["name"].tolist(), key=f"row_{i}")
        if row_name != "":
            selected_row = players_df.loc[players_df["name"] == row_name]["name"].values[0]
            selected_rows.append(selected_row)

    submit_button = st.button("Submit")
    return selected_rows, submit_button

# Write the form submission to the Google Sheet
def write_to_google_sheet(submission):
    sheet = client.open_by_url(sheet_url).sheet1
    for row in submission:
        row_without_comma = row.replace(",", "") 
        sheet.append_row([row_without_comma])

# Convert last_yr_pts to float
players_df['last_yr_pts'] = players_df['last_yr_pts'].astype(float)

# Main Streamlit code
def main():
    sorted_df = players_df.sort_values(by='last_yr_pts', ascending=False)
    st.subheader("Holdout Eligible Players")
    st.dataframe(sorted_df, use_container_width=True, hide_index=True,      
        column_config={
        "name": "Player",    
        "franchise_name": "Franchise",
        "position": "Position",
        "contract_year": "Years Remaining",
        "last_yr_pts": st.column_config.NumberColumn(
                "2023 Points",
                format="%.2f"),  
        "salary": st.column_config.NumberColumn(
            "Salary",
            format="$%d")
    },
        column_order=("name", "position", "salary", "contract_year", "franchise_name", "last_yr_pts") )
    
    st.title("Holdouts Ballot")

    selected_rows, submit_button = create_form()

    if submit_button:
        # selected_data = holdouts_df.iloc[selected_rows]
        # st.write(selected_rows)
        write_to_google_sheet(selected_rows)
        st.success("Form submitted successfully!")

if __name__ == "__main__":
    main()












import numpy as np
import pandas as pd
import streamlit as st
import json
import global_vars
import functions
import gspread
# import config
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(layout="wide")
st.title("2025 Holdouts")
st.divider()

import streamlit as st

st.set_page_config(layout="wide")
st.header("Player Grid")

image_list = [
    {
        "url": "https://www49.myfantasyleague.com/player_photos_2014/15710_thumb.jpg",
        "caption": "Kyren Williams."
    },
    {
        "url": "https://www49.myfantasyleague.com/player_photos_2014/16150_thumb.jpg",
        "caption": "CJ Stroud."
    },
    {
        "url": "https://www49.myfantasyleague.com/player_photos_2014/16181_thumb.jpg",
        "caption": "Chase Brown."
    },
    {
        "url": "https://www49.myfantasyleague.com/player_photos_2014/15290_thumb.jpg",
        "caption": "Nico Collins."
    },
]

# --- Create the grid layout ---

# Create the first row with two columns and a large gap between them
row1_col1, row1_col2 = st.columns(2, gap="large")

# Place the first two images in the first row
with row1_col1:
    # Set a specific width instead of using column width
    st.image(image_list[0]["url"], caption=image_list[0]["caption"], width=200)

with row1_col2:
    st.image(image_list[1]["url"], caption=image_list[1]["caption"], width=200)


# Create the second row with two columns
row2_col1, row2_col2 = st.columns(2, gap="large")

# Place the next two images in the second row
with row2_col1:
    st.image(image_list[2]["url"], caption=image_list[2]["caption"], width=200)

with row2_col2:
    st.image(image_list[3]["url"], caption=image_list[3]["caption"], width=200)
#####################################################
# VOTING
######################################################

# # Get the holdout list picks 
# players = functions.bq_query("SELECT * FROM `mfl-374514.dbt_production.dim_holdout_players`")
# players_df = pd.DataFrame(players)

# # Load the Google Sheets credentials
# # scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# # creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(config.google_credentials, strict=False), scope)
# scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# creds_dict = st.secrets["google_credentials"] # Assuming you're using st.secrets
# creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

# # Initialize the Google Sheets client
# client = gspread.authorize(creds)

# # Define the Google Sheet destination URL 
# sheet_url = global_vars.holdouts_voting_sheet_url

# franchises = functions.bq_query("SELECT franchise_name FROM `mfl-374514.dbt_production.dim_franchises`")
# franchises_df = pd.DataFrame(franchises)

# # Create the Streamlit form
# def create_form():
#     selected_rows = []

#     # Start the form
#     with st.form("voting_form"):
#         st.subheader("Who is voting?")
#         team_name = st.selectbox("Team Name", franchises_df)
#         selected_rows.append(team_name)
        
#         for i in range(5):
#             st.subheader(f"Holdout {i+1}")
#             row_name = st.selectbox(f"Select a Player", [""] + players_df["name"].tolist(), key=f"row_{i}")
#             if row_name != "":
#                 selected_row = players_df.loc[players_df["name"] == row_name]["name"].values[0]
#                 selected_rows.append(selected_row)

#         # Submit button inside the form
#         submit_button = st.form_submit_button("Submit")

#     return selected_rows, submit_button


# # Write the form submission to the Google Sheet
# def write_to_google_sheet(submission):
#     sheet = client.open_by_url(sheet_url).sheet1
#     for row in submission:
#         row_without_comma = row.replace(",", "") 
#         sheet.append_row([row_without_comma])

# # Convert last_yr_pts to float
# players_df['last_yr_pts'] = players_df['last_yr_pts'].astype(float)

# # Main Streamlit code
# def main():
#     sorted_df = players_df.sort_values(by='last_yr_pts', ascending=False)
#     st.subheader("Holdout Eligible Players")
#     st.dataframe(sorted_df, use_container_width=True, hide_index=True,      
#         column_config={
#         "name": "Player",    
#         "franchise_name": "Franchise",
#         "position": "Position",
#         "contract_year": "Years Remaining",
#         "last_yr_pts": st.column_config.NumberColumn(
#                 "2024 Points",
#                 format="%.2f"),  
#         "salary": st.column_config.NumberColumn(
#             "Salary",
#             format="$%d")
#     },
#         column_order=("name", "position", "salary", "contract_year", "franchise_name", "last_yr_pts") )
    
#     st.title("Holdouts Ballot")

#     selected_rows, submit_button = create_form()

#     if submit_button:
#         # selected_data = holdouts_df.iloc[selected_rows]
#         # st.write(selected_rows)
#         write_to_google_sheet(selected_rows)
#         st.success("Form submitted successfully!")

# if __name__ == "__main__":
#     main()












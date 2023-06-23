import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import config
import global_vars

site_token = config.key

st.set_page_config(layout="wide")
st.title("2023 Holdouts Voting")
st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

# Get the current rosters
r = requests.get(url = global_vars.rosters_URL, headers={'Authorization': 'Bearer ' + site_token }) 
rosters = r.json()
keep_cols = ["mfl_id", "franchise_name", "salary", "contract_years", "status"]
rosters_df = pd.DataFrame(rosters)[keep_cols]
rosters_df['mfl_id'] = rosters_df['mfl_id'].astype(str)

# Get player metadata
r = requests.get(url = global_vars.players_url) 
players = r.json()["players"]["player"]
keep_cols = ["position", "id", "name"]
players_df = pd.DataFrame(players)[keep_cols]

# Join player dfs
players_df1 = rosters_df.merge(players_df, how = 'left', left_on = 'mfl_id', right_on = 'id').drop(['id'], axis=1)

# Filter for Holdout Eligible Players 
holdouts_df = players_df1.loc[players_df1["mfl_id"].isin(global_vars.holdouts_2023)].sort_values(by=["salary"], ascending = False).drop(['mfl_id', 'status'], axis=1)


# Create the Streamlit form
def create_form():
    selected_rows = []
    for i in range(5):
        st.subheader(f"Holdout {i+1}")
        row_name = st.selectbox(f"Select a Player", [""] + holdouts_df["name"].tolist(), key=f"row_{i}")
        if row_name != "":
            selected_row = holdouts_df.loc[holdouts_df["name"] == row_name]
            selected_rows.append(selected_row)
    submit_button = st.button("Submit")
    return selected_rows, submit_button


# Main Streamlit code
def main():
    st.title("Holdout Eligible Players")
    st.dataframe(holdouts_df, use_container_width=True, hide_index=True,      
        column_config={
        "name": "Player",    
        "franchise_name": "Franchise",
        "position": "Position",
        "contract_years": "Years Remaining",
        "salary": st.column_config.NumberColumn(
            "Salary",
            format="$%d")
    })
    st.title("Holdouts Ballot")

    selected_rows, submit_button = create_form()

    if submit_button:
        selected_data = holdouts_df.iloc[selected_rows]
        # write_to_google_sheet(selected_data.values.tolist())
        st.success("Form submitted successfully!")

if __name__ == "__main__":
    main()
################


# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import json
# import secrets

# # Load the Google Sheets credentials
# scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(secrets.google_credentials), scope)



# # Initialize the Google Sheets client
# client = gspread.authorize(creds)

# # Define the Google Sheet destination URL (replace with your actual URL)
# sheet_url = secrets.google_sheet_url


# # Write the form submission to the Google Sheet
# def write_to_google_sheet(submission):
#     sheet = client.open_by_url(sheet_url).sheet1
#     for row in submission:
#         sheet.append_row(row.values.tolist())

# # Main Streamlit code
# def main():
#     st.title("Select and Submit Rows from holdouts_df")

#     selected_rows, submit_button = create_form()

#     if submit_button:
#         write_to_google_sheet(selected_rows)
#         st.success("Form submitted successfully!")

# if __name__ == "__main__":
#     main()



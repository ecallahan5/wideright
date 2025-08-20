import pandas as pd
import streamlit as st
import requests
import json
import config
import functions
import global_vars


st.set_page_config(layout="wide")
st.title("Annual Free Extension Eligibility")
st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

st.write("See you in 2024!")

# # Get the list of teams
# franchises = api_calls.get_teams()
# keep_cols = ["mfl_id", "division", "franchise_name", "icon_url"]
# df_franchises = pd.DataFrame(franchises)[keep_cols]

# # Who has already done one?
# extensions_df = api_calls.get_extensions()
# free_ext = extensions_df.loc[extensions_df["extension_type"] == 'free'][["player", "franchise", "length"]]
# free_ext_teams = free_ext["franchise"].tolist()


# team = st.selectbox(
#     '**Which Team is Extending a Player?**', [""] + sorted(df_franchises["franchise_name"].unique()))

# if team in free_ext_teams:
#     player = free_ext.loc[free_ext["franchise"] == team]["player"].values[0]
#     term = free_ext.loc[free_ext["franchise"] == team]["length"].values[0]
#     st.subheader(str(team)+" has already given "+str(player)+" an extension of "+str(term)+" years." )

# else:
#     # Get the current rosters
#     rosters = api_calls.get_rosters()
#     keep_cols = ["mfl_id", "franchise_name", "salary", "contract_years", "status"]
#     rosters_df = pd.DataFrame(rosters)[keep_cols]
#     rosters_df = rosters_df.loc[rosters_df["status"] != 'TAXI_SQUAD']
#     rosters_df['mfl_id'] = rosters_df['mfl_id'].astype(str)

#     # Get player metadata
#     players = api_calls.get_players_wr()
#     keep_cols = ["position", "mfl_id", "first_name", "last_name"]
#     players_df = pd.DataFrame(players)[keep_cols]
#     players_df["mfl_id"] = players_df["mfl_id"].astype(str)


#     try:
#         # Join player dfs
#         players_df1 = rosters_df.merge(players_df, how = 'left', on = 'mfl_id')
#         players_df1['position_order'] = players_df1['position'].map(global_vars.sort_mapping['index'])
#         filtered_df = players_df1.loc[(players_df1["franchise_name"] == team) & ((players_df1["contract_years"]) == 1)]
#         filtered_df = filtered_df.rename(columns={"first_name": "First Name", "last_name": "Last Name","position": "Position", "salary": "Salary"}).sort_values('position_order')
#         table_cols = ["First Name", "Last Name", "Position", "Salary "]
#         filtered_df["Salary"] = filtered_df["Salary"].apply("${:,.2f}".format)

#         player = st.radio("Here is who is eligible to be extended", filtered_df["First Name"] + " " + filtered_df["Last Name"] + " - " + filtered_df["Position"],\
#                 captions = filtered_df["Salary"])

#         st.divider()
#         selected_salary = filtered_df.loc[filtered_df["First Name"] + " " + filtered_df["Last Name"] + " - " + filtered_df["Position"] == player]["Salary"].values[0]

#         def calculate_updated_value(selected_salary, constant):
#             # Get the value from the specified column
#             value_str = selected_salary
            
#             # Remove the dollar sign if it exists
#             value_str = value_str.replace('$', '')

#             try:
#                 # Convert the modified string to a float
#                 value = float(value_str)
                
#                 # Calculate the updated value
#                 updated_value = value * constant

#                 # Format the updated value as USD currency
#                 formatted_value = updated_value = f"${updated_value:.2f}"

#                 return formatted_value
#             except ValueError:
#                 return None  

#         st.subheader("Extension Options for "+str(player) )
#         col1, col2, col3 = st.columns(3, gap = "large")

#         with col1:
#             st.metric("1 Year", calculate_updated_value(selected_salary, 1.15))
#         with col2:
#             st.metric("2 Year", calculate_updated_value(selected_salary, 1.30))
#         with col3:    
#             st.metric("3 Year", calculate_updated_value(selected_salary, 1.45))

#     except:
#         st.write("Please select a team above")        
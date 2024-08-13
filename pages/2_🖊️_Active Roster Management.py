import numpy as np
import pandas as pd
import streamlit as st
import json
import plotly.express as px
import config
import global_vars
import functions


st.set_page_config(layout="wide")
st.title("Roster Construction")
st.divider()
st.image("https://as2.ftcdn.net/v2/jpg/00/89/02/67/1000_F_89026793_eyw5a7WCQE0y1RHsizu41uhj7YStgvAA.jpg")


# # Get the current rosters
# rosters = functions.bq_query("SELECT c.name as franchise_name, a.player_id, contract_year, salary, team, b.name, position  \
#                               FROM `mfl-374514.dbt_production.fct_rosters` a \
#                              left join `mfl-374514.dbt_production.fct_players`  b\
#                              on a.player_id = b.player_id \
#                              left join mfl-374514.dbt_production.fct_franchises c \
#                              on a.franchise_id = c.franchise_id\
#                              where a.status != 'TAXI_SQUAD' ")
# rosters_df = pd.DataFrame(rosters)
# rosters_df

# col1, col2 = st.columns(2)

# with col1:
#     # Team picker
#     team = st.selectbox(
#         '**Choose a team**',
#         sorted(rosters_df["franchise_name"].unique()))
    
# with col2:
#     # Year Picker
#         year = st.selectbox(
#         '**Choose a league year**',
#         global_vars.yr_list)

# st.divider()

# #####################################

# contract_yrs = global_vars.zipped_df.loc[global_vars.zipped_df["Year"] == year]["Contract Length"].values[0]
# filtered_df = players_df1.loc[(players_df1["franchise_name"] == team) & ((players_df1["contract_years"]) >= contract_yrs)]
# filtered_df["salary1"] = filtered_df["salary"].apply("${:,.2f}".format)
# filtered_df['position_order'] = filtered_df['position'].map(global_vars.sort_mapping['index'])
# filtered_df = filtered_df.rename(columns={"first_name": "First Name", "last_name": "Last Name","position": "Position", "salary": "Salary"}).sort_values('position_order')

# # Table style
# st.markdown(global_vars.hide_table_row_index, unsafe_allow_html=True)
# table_cols = ["First Name", "Last Name", "Position", "Salary"]
# st.subheader("Rosters")
# st.dataframe(filtered_df[table_cols], use_container_width=True, hide_index=True)

# st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

# cap_used = "${:,.2f}".format(filtered_df["Salary"].sum())
# contract_yrs_used = filtered_df["contract_years"].sum()
# roster_spots_used = filtered_df["mfl_id"].count()

# cap_space = "${:,.2f}".format(global_vars.salary_cap - filtered_df["Salary"].sum())
# contract_yrs_free = global_vars.contract_cap - contract_yrs_used
# roster_spots_free = global_vars.roster_size - roster_spots_used

# col1, col2, col3, col4, col5 = st.columns(5)

# #Cap Dollars
# col1.subheader("Salary Cap")
# col1.image(global_vars.dollar_icon)
# col1.metric("Cap Used", cap_used)
# col1.metric("Cap Space", cap_space)

# # Contract Years
# col3.subheader("Contracts")
# col3.image(global_vars.contract_icon)
# col3.metric("Contract Years Used", contract_yrs_used)
# col3.metric("Contract Years Free", contract_yrs_free)

# #Roster Spots
# col5.subheader("Roster Spots")
# col5.image(global_vars.player_icon)
# col5.metric("Roster Spots Used", roster_spots_used)
# col5.metric("Roster Spots Free", roster_spots_free)

# with st.expander("Positional Breakdowns"):
#     pos1, pos2, pos3= st.columns(3)

#     fig = px.pie(filtered_df, values= filtered_df["Salary"], names= filtered_df["Position"], title='Cap Dollars by Position')
#     fig.update_traces(textposition='inside', textinfo='value')
#     pos1.plotly_chart(fig, use_container_width=True)

#     fig = px.pie(filtered_df, values= filtered_df["contract_years"], names= filtered_df["Position"], title='Contract Years by Position')
#     fig.update_traces(textposition='inside', textinfo='value')
#     pos2.plotly_chart(fig, use_container_width=True)

#     roster_values = filtered_df["mfl_id"].value_counts()
#     fig = px.pie(filtered_df, values= roster_values, names= filtered_df["Position"], title='Roster Spots by Position')
#     fig.update_traces(textposition='inside', textinfo='value')
#     pos3.plotly_chart(fig, use_container_width=True)






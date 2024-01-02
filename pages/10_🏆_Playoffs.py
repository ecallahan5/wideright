import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import config
import global_vars
import api_calls
import plotly.express as px
import plotly.graph_objects as go

# Things to use during regular season

# seeds = pd.DataFrame({
#      'Seed': [1,2,3,4,5,6],
#      'Team': []
#      })
# st.dataframe(seeds, hide_index=True, use_container_width = True)

# seeds = pd.DataFrame({
#      'Seed': [1,2,3,4,5,6],
#      'Team': [)
# st.dataframe(seeds, hide_index=True, use_container_width = True)

st.set_page_config(layout="wide")
st.title("Playoffs ")
st.header("Championship Bracket", divider=True)

# Get the list of teams
franchises = api_calls.get_teams()
keep_cols = ["mfl_id", "division", "franchise_name", "icon_url"]
df_franchises = pd.DataFrame(franchises)[keep_cols]

champ_df = pd.DataFrame(

     [{"seed": 4,"franchise_id":"0007","Champ":0.2346,"Runner-Up":0.7654,"3rd place":0},
     {"seed": 3,"franchise_id":"0002","Champ":0,"Runner-Up":0,"3rd place":0.4471},
     {"seed": 1,"franchise_id":"0006","Champ":0.7654,"Runner-Up":0.2346,"3rd place":0},
     {"seed": 2,"franchise_id":"0001","Champ":0,"Runner-Up":0,"3rd place":0.5529}]
 )

champ_df = champ_df.merge(df_franchises, left_on = 'franchise_id', right_on = 'mfl_id')

st.subheader('This Week\'s Games', divider=False)

with st.expander("Click for Previews"):
     with st.container(border = True):
          col1, col2, col3, col4, col5 = st.columns(5)
          col1.metric("Maize \'N Blue", "#4")
          col2.metric('Win %', "23%")
          col3.write("Prediction")
          col3.image(champ_df.loc[champ_df["seed"] == 2]["icon_url"].values[0])
          col4.metric('Win %', "77%")
          col5.metric("The Uncaught Exceptions", "#2")
     with st.container(border = True):
          col1, col2, col3, col4, col5= st.columns(5)
          col1.metric("Brooklyn Big Blue", "#3")
          col2.metric('Win %', "53%")
          col3.write("Prediction")
          col3.image(champ_df.loc[champ_df["seed"] == 3]["icon_url"].values[0])
          col4.metric('Win %', "47%")
          col5.metric("The Van Buren Boys", "#1")
st.divider()
# # Page Grid layout
# def make_custom_grid(cols,rows):
#     grid = [0]*cols
#     for i in range(cols):
#         with st.container():
#             grid[i] = st.columns(rows)
#     return grid

# grid_row_count = 6
# grid_col_count = 3

# mygrid = make_custom_grid(grid_row_count,grid_col_count)

# mygrid[0][0].subheader("Wild Card", divider = True)
# mygrid[0][1].subheader("Semi Finals", divider = True)
# mygrid[0][2].subheader("Finals", divider = True)

# for row_num in list(range(grid_row_count)):
#     for col_num in list(range(grid_col_count)):
          
#           mygrid[row_num][col_num].write("penus")
st.subheader('Bracket', divider=False)
with st.expander("Click for Bracket"):

     col2, col3 = st.columns(2)

     # with col1:
     #      st.subheader("Wild Card", divider = False)
     #      with st.container(border = True):
     #           st.image(champ_df.loc[champ_df["seed"] == 6]["icon_url"].values[0])
     #      with st.container():
     #           st.write("")
     #      with st.container(border = True):
     #           st.image(champ_df.loc[champ_df["seed"] == 3]["icon_url"].values[0])
     #      st.divider()  
     #      with st.container(border = True):
     #           st.image(champ_df.loc[champ_df["seed"] == 5]["icon_url"].values[0])
     #      with st.container():
     #           st.write(" ")
     #      with st.container(border = True):
     #           st.image(champ_df.loc[champ_df["seed"] == 4]["icon_url"].values[0])
          
     with col2:
          st.subheader("Semi Finals", divider = True)
          with st.container(border = True):
               st.image(champ_df.loc[champ_df["seed"] == 3]["icon_url"].values[0])
          with st.container(border = True):
               st.image(champ_df.loc[champ_df["seed"] == 2]["icon_url"].values[0])
          st.divider()  
          with st.container(border = True):
               st.image(champ_df.loc[champ_df["seed"] == 4]["icon_url"].values[0])
          with st.container(border = True):
               st.image(champ_df.loc[champ_df["seed"] == 1]["icon_url"].values[0])

     with col3:    
          st.subheader("Finals", divider = True)
          with st.container(border = True):
               st.image(champ_df.loc[champ_df["seed"] == 4]["icon_url"].values[0])
          with st.container(border = True):
               st.image(champ_df.loc[champ_df["seed"] == 2]["icon_url"].values[0])


st.divider()

st.subheader('Title Chances', divider=False)
with st.expander("Click for Title Chances"):
     df_ch = champ_df.rename(columns={"franchise_name" : "Team", "Champ" : "Probability"})
     st.bar_chart(df_ch, x='Team', y='Probability')


st.header("Consolation Bracket", divider=True)

cons_df = pd.DataFrame(

[{"seed": 4,"franchise_id":"0010","Extra Pick":0},
 {"seed": 6,"franchise_id":"0005","Extra Pick":0},
 {"seed": 1,"franchise_id":"0012","Extra Pick":0.5169},
 {"seed": 2,"franchise_id":"0003","Extra Pick":0.4831}]
)

cons_df = cons_df.merge(df_franchises, left_on = 'franchise_id', right_on = 'mfl_id')


st.subheader('Bracket', divider=False)
with st.expander("Click for Bracket"):

     col2, col3 = st.columns(2)

     # with col1:
     #      st.subheader("Wild Card", divider = False)
     #      with st.container(border = True):
     #           st.image(cons_df.loc[cons_df["seed"] == 6]["icon_url"].values[0])
     #      with st.container():
     #           st.write("")
     #      with st.container(border = True):
     #           st.image(cons_df.loc[cons_df["seed"] == 3]["icon_url"].values[0])
     #      st.divider()  
     #      with st.container(border = True):
     #           st.image(cons_df.loc[cons_df["seed"] == 5]["icon_url"].values[0])
     #      with st.container():
     #           st.write(" ")
     #      with st.container(border = True):
     #           st.image(cons_df.loc[cons_df["seed"] == 4]["icon_url"].values[0])
          
     with col2:
          st.subheader("Semi Finals", divider = True)
          with st.container(border = True):
               st.image(cons_df.loc[cons_df["seed"] == 4]["icon_url"].values[0])
          with st.container(border = True):
               st.image(cons_df.loc[cons_df["seed"] == 2]["icon_url"].values[0])
          st.divider()  
          with st.container(border = True):
               st.image(cons_df.loc[cons_df["seed"] == 6]["icon_url"].values[0])
          with st.container(border = True):
               st.image(cons_df.loc[cons_df["seed"] == 1]["icon_url"].values[0])
     with col3:    
          st.subheader("Finals", divider = True)
          with st.container(border = True):
               st.image(cons_df.loc[cons_df["seed"] == 2]["icon_url"].values[0])
          with st.container(border = True):
               st.image(cons_df.loc[cons_df["seed"] == 1]["icon_url"].values[0])


st.divider()

st.subheader('Extra Pick Chances', divider=False)
with st.expander("Click for Extra Pick Chances"):
     df_ch = cons_df.rename(columns={"franchise_name" : "Team", "Extra Pick" : "Probability"})
     st.bar_chart(df_ch, x='Team', y='Probability')

##################################################################






# st.markdown("""---""")
# st.header('Expected Playoff Winnings')
# df_money = pd.DataFrame({
#      'Team': [ "Moneyballers", "The Van Buren Boys",  "Brooklyn Big Blue", "The Uncaught Exceptions"],
#      '$$': [241, 254, 37, 23]
#      })
# st.bar_chart(df_money, x='Team', y='$$')


# st.markdown("""---""")
# st.header('Extra Pick!')
# # dfl = pd.DataFrame({
# #      'Team': ["You Carr'd Be Kidding", "Hidden Talents", "Hurricane",  "Shoot em Into the Sun"],
# #      'Probability': [37.05, 33.88, 21.13, 7.94]
# #      })
# # st.bar_chart(dfl, x='Team', y='Probability')

# pick = pd.DataFrame({
#      'Team': ["Hidden Talents", "Hurricane"],
#      'Win Probability': [52, 48]
#      })
# fig = px.pie(pick, values='Win Probability', names='Team', title='Extra Pick')
# st.plotly_chart(fig, use_container_width=True)

# ####################

###### FOR LATER #############

# st.header('Championship Bracket')
# champ = pd.DataFrame({
#      'Team': ["The Van Buren Boys", "Moneyballers"],
#      'Win Probability': [53.86, 46.14]
#      })
# fig = px.pie(champ, values='Win Probability', names='Team', title='Championship Game')
# st.plotly_chart(fig, use_container_width=True)

# third = pd.DataFrame({
#      'Team': ["Brooklyn Big Blue", "The Uncaught Exceptions"],
#      'Win Probability': [61.71, 38.29]
#      })
# fig = px.pie(third, values='Win Probability', names='Team', title='Third Place')
# st.plotly_chart(fig, use_container_width=True)

# # st.header('Road to the Title!')
# # fig = go.Figure(data=[go.Sankey(

# #     # Define nodes
# #     node = dict(
# #       pad = 50,
# #       thickness = 5,
# #       line = dict(color = "black", width = 0.5),
# #       label =  ["Brooklyn Big Blue", "The Uncaught Exceptions", "Moneyballers", "The Van Buren Boys", "Championship Game", "Consolation Game", \
# #               "1st Place", "2nd Place", "3rd Place", "4th Place"],
# #       color =  ["Blue", "Red", "Green", "Purple"]
# #     ),
# #     # Add links
# #     link = dict(
# #       source =  [0, 0, 1, 1, 2, 2, 3, 3, 4,4,4,4,4,4,4,4,5,5,5,5,5,5,5,5,],
# #       target =  [4, 5, 4, 5, 4, 5, 4, 5, 6,7,8,9, 6,7,8,9, 6,7,8,9, 6,7,8,9],
# #       value =  [70, 30, 65, 35, 35, 65, 30, 70, 47, 23, 21, 9, 29, 36, 19, 16, 11, 24, 26, 39, 13, 17, 34, 36 ],
# #       label =  ["Brooklyn Big Blue Wins", "Brooklyn Big Blue Loses", "The Uncaught Exceptions Wins", "The Uncaught Exceptions Loses", \
# #                "Moneyballers Wins", "Moneyballers Loses", "The Van Buren Boys Wins", "The Van Buren Boys",
# #                "Brooklyn Big Blue 1st", "Brooklyn Big Blue 2nd", "Brooklyn Big Blue 3rd", "Brooklyn Big Blue 4th", \
# #                "The Uncaught Exceptions 1st", "The Uncaught Exceptions 2nd", "The Uncaught Exceptions 3rd", "The Uncaught Exceptions 4th", \
# #                "Moneyballers 1st", "Moneyballers 2nd", "Moneyballers 3rd", "Moneyballers 4th", \
# #                "The Van Buren Boys 1st", "The Van Buren Boys 2nd", "The Van Buren Boys 3rd", "The Van Buren Boys 4th"   ],
# #       color =  ["Blue", "Blue", "Red", "Red", "Green", "Green", "Purple", "Purple", \
# #                   "Blue", "Blue", "Blue", "Blue", "Red", "Red", "Red", "Red", \
# #                     "Green", "Green", "Green", "Green",  "Purple", "Purple", "Purple", "Purple"]
# # ))])





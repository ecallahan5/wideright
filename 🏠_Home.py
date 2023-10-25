import streamlit as st
import api_calls
import global_vars
from datetime import datetime

st.title("Welcome to Wide Right")
st.image("https://www.si.com/.image/c_limit%2Ccs_srgb%2Cq_auto:good%2Cw_298/MTY4MjYzMjM1MjkyODk4NTgx/scott-norwoodgif.webp")
st.divider()

st.header("Important Dates")

# Convert the string to a datetime object
taxi_date = datetime.strptime(global_vars.taxi_dl, '%Y-%m-%d')
trade_date = datetime.strptime(global_vars.trade_dl, '%Y-%m-%d')

# Format the datetime object as 'Month Day, Year'
formatted_taxi_dl = taxi_date.strftime('%B %d, %Y')
formatted_trade_dl = trade_date.strftime('%B %d, %Y')

# Days Left
current_date = datetime.now()
taxi_days_left = (taxi_date - current_date).days
trade_days_left = (trade_date - current_date).days


st.subheader("Taxi Claims end on "+str(formatted_taxi_dl))
st.caption(str(taxi_days_left)+" days left!")
st.subheader("Trades and Extensions end on "+str(formatted_trade_dl))
st.caption(str(trade_days_left)+" days left!")

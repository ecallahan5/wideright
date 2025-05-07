import streamlit as st
import global_vars
from datetime import datetime

st.title("Welcome to Wide Right 2025!")
st.image("https://s.yimg.com/ny/api/res/1.2/QJcrvuxEPZLQX4n3kjaa2g--/YXBwaWQ9aGlnaGxhbmRlcjt3PTI0MDA7aD0xNjI4O2NmPXdlYnA-/https://s.yimg.com/os/creatr-images/2019-02/9c91c250-2653-11e9-bfee-96db584edaa1")
st.divider()

st.subheader("Updated Content Coming Soon ...")

# st.header("Important Dates")

# # Convert the string to a datetime object
# taxi_date = datetime.strptime(global_vars.taxi_dl, '%Y-%m-%d')
# trade_date = datetime.strptime(global_vars.trade_dl, '%Y-%m-%d')

# # Format the datetime object as 'Month Day, Year'
# formatted_taxi_dl = taxi_date.strftime('%B %d, %Y')
# formatted_trade_dl = trade_date.strftime('%B %d, %Y')

# # Days Left
# current_date = datetime.now()
# taxi_days_left = (taxi_date - current_date).days +1
# trade_days_left = (trade_date - current_date).days +1

# if current_date > taxi_date:
#     st.subheader("Taxi Claims are closed!")
# else:
#     st.subheader("Taxi Claims end on "+str(formatted_taxi_dl))
#     st.caption(str(taxi_days_left)+" days left!")

# if current_date > trade_date:
#     st.subheader("Trades and Extenstions are closed!")
# else:
#     st.subheader("Trades and Extensions end on "+str(formatted_trade_dl))
#     st.caption(str(trade_days_left)+" days left!")

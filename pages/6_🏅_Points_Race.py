import streamlit as st
import api_calls
import global_vars

st.set_page_config(layout="wide")
st.title("Points Race")
st.markdown("""<hr style="height:10px;border:none;color:#333;background-color:#333;" /> """, unsafe_allow_html=True)

st.image(global_vars.coming_soon)

# Get Probabilities
# probs_df = api_calls.get_probs()
# st.write(probs_df)
import pandas as pd
import streamlit as st
import requests
import functions
import global_vars

st.set_page_config(layout="wide")
st.title("Annual Free Extension Eligibility")
st.divider()

# Which players are eligible to be given a free extension?
ext_eligible = functions.bq_query("SELECT * FROM `mfl-374514.dbt_ecallahan.dim_free_ext_elig`")
ext_eligible_df = pd.DataFrame(ext_eligible)
ext_eligible_df['position_order'] = ext_eligible_df['position'].map(global_vars.sort_mapping['index'])
ext_eligible_df = ext_eligible_df.rename(columns={"player_name": "Name","position": "Position", "salary": "Salary"}).sort_values('position_order')
ext_eligible_df["Salary"] = ext_eligible_df["Salary"].apply("${:,.2f}".format)

team = st.selectbox(
    '**Which Team is Extending a Player?**', sorted(ext_eligible_df["franchise_name"].unique()), \
        index=None, placeholder="Choose a team")

team_elig = ext_eligible_df.loc[ext_eligible_df["franchise_name"] == team]

if team:
    player = st.radio("Here is who is eligible to be extended", team_elig["Name"] + " - " + team_elig["Position"],\
        captions = team_elig["Salary"], horizontal=True)
    
    st.divider()
    st.subheader("Extension Options for "+str(player) )

    salary = team_elig.loc[team_elig["Name"] + " - " + team_elig["Position"] == player]["Salary"].values[0]
    ext_1_min = 5
    ext_2_min = 12
    ext_3_min = 24
    ext_1_salary = f"${max(functions.calculate_updated_value(salary, 1.15), ext_1_min):.2f}"
    ext_2_salary = f"${max(functions.calculate_updated_value(salary, 1.30), ext_2_min):.2f}"
    ext_3_salary = f"${max(functions.calculate_updated_value(salary, 1.45), ext_3_min):.2f}"

    col1, col2, col3 = st.columns(3, gap = "large")

    with col1:
        st.metric("1 Year", ext_1_salary)
    with col2:
        st.metric("2 Year", ext_2_salary)
    with col3:    
        st.metric("3 Year", ext_3_salary)

    st.divider()
    with st.chat_message("Norwood", avatar=global_vars.norwood_avatar):
        st.write("Would you like to extend " + player + "?")
        extend = st.checkbox("Yes!")
        if extend: 
            ext_length = st.radio("How many years would you like to extend " + player + "?", [1,2,3], horizontal=True)
            if ext_length == 1: 
                ext_salary = ext_1_salary
                if functions.calculate_updated_value(salary, 1) < ext_1_min: 
                    adj_needed = True
                else: 
                    adj_needed = False
            if ext_length == 2: 
                ext_salary = ext_2_salary
                if functions.calculate_updated_value(salary, 1) < ext_2_min: 
                    adj_needed = True
                else: 
                    adj_needed = False
            if ext_length == 3: 
                ext_salary = ext_3_salary
                if functions.calculate_updated_value(salary, 1) < ext_3_min: 
                    adj_needed = True
                else: 
                    adj_needed = False
            if adj_needed:
                st.warning("""The current contract is below the minimum required to execute this extension. 
                           If you would like to proceed, this year\'s contract will immediately increase to """ + ext_salary + ".", icon="⚠️")
            st.divider()
            st.write(f"Would you like to extend {player} for {ext_length} years at a salary of {ext_salary}?")
            extend_action = st.button("Extend him!")
            if extend_action:
                webhook_url = 'https://discord.com/api/webhooks/1287066512745693235/q9xOKdmyjoPsrO8LrHLY700gGHVl5eGayY15hxet5EEFawNAbgxFK1VQF7SvQ1XCYlFg'
                # test_url = 'https://discord.com/api/webhooks/1275122704164323360/YXzGlV2DI1PQ8LtXSEo0bpgxiLg3hw-HPXDtaNopRyzXX1gdjay01Icx4HqzZrJfjB4z'
                if adj_needed: 
                    content = f"🚨 **ANNUAL FREE EXTENSION ALERT!** 🚨\n\n" \
                            f"**{team}** is extending **{player}** for **{ext_length} years** at a salary of **{ext_salary}**.\n\n" \
                            f"<@197385905638604800> will need to adjust the current year's salary."
                else:
                    content = f"🚨 **ANNUAL FREE EXTENSION ALERT!** 🚨\n\n" \
                            f"**{team}** is extending **{player}** for **{ext_length} years** at a salary of **{ext_salary}**."
                payload = {"content": content}
                r = requests.post(url = webhook_url, data = payload)
                if r: 
                    st.toast("Your claim has been submitted!", icon='🎉')
            



 
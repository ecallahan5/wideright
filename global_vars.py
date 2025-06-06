import datetime as dt
from datetime import datetime
import requests
import pandas as pd
import streamlit as st

# Endpoints
franchises_URL = "https://wideright.app/api/v1/franchises"
picks_URL = "https://www49.myfantasyleague.com/2023/export?TYPE=futureDraftPicks&L=59643&APIKEY=ahFi18iVvuWtx02mPVDHZTEeF7ox&JSON=1"
rosters_URL = "https://wideright.app/api/v1/rosters"
players_URL = 'https://www49.myfantasyleague.com/2023/export?TYPE=players&L=59643&APIKEY=&DETAILS=&SINCE=&PLAYERS=&JSON=1'
players_URL_wr = 'https://wideright.app/api/v1/players'
schedule_URL = 'https://wideright.app/api/v1/schedule'
probs_URL = 'https://wideright.app/api/v1/colab/playoff-model'
standings_URL = "https://wideright.app/api/v1/standings"
calendar_URL = 'https://www49.myfantasyleague.com/2023/export?TYPE=calendar&L=59643&APIKEY=ahFi18iVvuWsx1SmPVDHZTEeF7ox&JSON=1'
extensions_url = 'https://wideright.app/api/v1/contract-extensions'

#Images
dollar_icon = "https://icons.veryicon.com/png/o/business/business-icon-2/money-42.png"
contract_icon = "https://cdn-icons-png.flaticon.com/512/126/126249.png"
player_icon = "https://cdn-icons-png.flaticon.com/512/164/164457.png"
coming_soon = "https://media.istockphoto.com/id/1410983127/vector/under-construction-sign-and-label.jpg?s=612x612&w=0&k=20&c=8Ft81am5L7o1AAZ7SDPn3gi51ur_7cfrlU2au4_bptM="
norwood_avatar = avatar = "https://kubrick.htvapps.com/htv-prod-media.s3.amazonaws.com/images/scott-norwood-1486054177.jpg?crop=1.00xw:0.358xh;0,0.226xh&resize=900:*"

#League Year
cur_month = datetime.now().month
cur_yr = datetime.now().year
trade_dl = '2023-11-23'
taxi_dl = '2023-11-16'

if cur_month > 2:
    league_yr = cur_yr
else:
    league_yr = cur_yr-1

#League Data
@st.cache_data(ttl=dt.timedelta(days=1))
def get_league_mfl_data():
    league_url = f'https://www49.myfantasyleague.com/{league_yr}/export?TYPE=league&L=59643&APIKEY=&JSON=1'
    r = requests.get(url=league_url)
    r.raise_for_status()  # Raise an exception for bad status codes
    return r.json()["league"]

league = get_league_mfl_data()
# roster_size = int(league["rosterSize"])
roster_size = 20  # This seems to be a hardcoded override
salary_cap = float(league["salaryCapAmount"])
contract_cap = 42 # This is hardcoded
max_contract_yrs = 5

#Contract Years Lookup
yr_list = list(range(league_yr, league_yr+max_contract_yrs,1))
contract_yrs = list(range(1,max_contract_yrs+1,1))
zipped_list = list(zip(contract_yrs, yr_list))
cols = ["Contract Length", "Year"]
zipped_df = pd.DataFrame(zipped_list, columns = cols)

# Positional Order
df_mapping = pd.DataFrame({
    'positions': ['QB', 'RB', 'WR', 'TE', 'Def', 'PK'],
})
sort_mapping = df_mapping.reset_index().set_index('positions')

# Table Format
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            """

# Page Grid layout
def make_grid(cols,rows):
    grid = [0]*cols
    for i in range(cols):
        with st.container():
            grid[i] = st.columns(rows)
    return grid

# Setting up Current Week
def extract_values(obj, key):
    """Pull all values of specified key from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    return results


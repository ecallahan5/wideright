import datetime as dt
from datetime import datetime
import requests
import pandas as pd

league_id = 59643

# Endpoints
franchises_URL = "https://wideright.app/api/v1/franchises"
picks_URL = 'https://www49.myfantasyleague.com/2023/export?TYPE=futureDraftPicks&L='+str(league_id)+'&JSON=1'
rosters_URL = "https://wideright.app/api/v1/rosters"
players_url = 'https://www49.myfantasyleague.com/2023/export?TYPE=players&L='+str(league_id)+'&APIKEY=&DETAILS=&SINCE=&PLAYERS=&JSON=1'

#Images
dollar_icon = "https://icons.veryicon.com/png/o/business/business-icon-2/money-42.png"
contract_icon = "https://cdn-icons-png.flaticon.com/512/126/126249.png"
player_icon = "https://cdn-icons-png.flaticon.com/512/164/164457.png"

#League Year
cur_month = datetime.now().month
cur_yr = datetime.now().year

if cur_month > 2:
    league_yr = cur_yr
else:
    league_yr = cur_yr-1

#League Data
league_url = 'https://www49.myfantasyleague.com/'+str(league_yr)+'/export?TYPE=league&L='+str(league_id)+'&APIKEY=&JSON=1'
r = requests.get(url = league_url)
league = r.json()["league"]
roster_size = int(league["rosterSize"])
salary_cap = float(league["salaryCapAmount"])
contract_cap = 42
max_contract_yrs = 5

#Contract Years Lookup
yr_list = list(range(league_yr, league_yr+max_contract_yrs,1))
contract_yrs = list(range(1,max_contract_yrs+1,1))
zipped_list = list(zip(contract_yrs, yr_list))
cols = ["Contract Length", "Year"]
zipped_df = pd.DataFrame(zipped_list, columns = cols)

# Positional Order
df_mapping = pd.DataFrame({
    'positions': ['QB', 'RB', 'WR', 'TE', 'DEF', 'K'],
})
sort_mapping = df_mapping.reset_index().set_index('positions')


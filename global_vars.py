import datetime as dt
from datetime import datetime
import requests
import pandas as pd

# Endpoints
franchises_URL = "https://wideright.app/api/v1/franchises"
picks_URL = "https://www49.myfantasyleague.com/2023/export?TYPE=futureDraftPicks&L=59643&APIKEY=ahFi18iVvuWtx02mPVDHZTEeF7ox&JSON=1"
rosters_URL = "https://wideright.app/api/v1/rosters"
players_url = 'https://www49.myfantasyleague.com/2023/export?TYPE=players&L=59643&APIKEY=&DETAILS=&SINCE=&PLAYERS=&JSON=1'

#League Year
cur_month = datetime.now().month
cur_yr = datetime.now().year

if cur_month > 2:
    league_yr = cur_yr
else:
    league_yr = cur_yr-1

#League Data
league_url = 'https://www49.myfantasyleague.com/'+str(league_yr)+'/export?TYPE=league&L=59643&APIKEY=&JSON=1'
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


import os
import sys
import dlt
from dlt.sources.helpers import requests
from .common import _create_auth_headers, create_dlt_pipeline

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (where config.py is)
parent_dir = os.path.dirname(script_dir)
# Add parent directory to sys.path
sys.path.insert(0, parent_dir)

# Now import config
import config
from global_vars import host, league_id, league_year, last_league_year


@dlt.resource(write_disposition="replace")
def sourcename_resource(api_secret_key=dlt.secrets.value):
    headers = _create_auth_headers(api_secret_key)

    # check if authentication headers look fine
    print(headers)

    # make an api call here
    url = f"https://{host}/{league_year}/export?TYPE=schedule&L={league_id}&APIKEY={config.mfl_api_key}&W=&F=&JSON=1"
    response = requests.get(url)
    response.raise_for_status()
    yield response.json()

@dlt.source
def sourcename_source(sourcename_resource_func=dlt.secrets.value):
    yield sourcename_resource_func


if __name__ == "__main__":
    create_dlt_pipeline(
        pipeline_name='mfl_schedule',
        dataset_name='schedule',
        resource_func=sourcename_resource,
        source_func=sourcename_source
    )

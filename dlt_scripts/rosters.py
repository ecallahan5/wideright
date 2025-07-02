import os
import dlt
from dlt.sources.helpers import requests
from .common import _create_auth_headers, create_dlt_pipeline
from global_vars import host, league_id, league_year


@dlt.resource(write_disposition="replace")
def rosters_resource(mfl_api_key=dlt.secrets.value):
    # headers = _create_auth_headers(mfl_api_key) # Not used by MFL API if key is in URL
    # print(headers)

    # make an api call here
    url = f"https://{host}/{league_year}/export?TYPE=rosters&L={league_id}&APIKEY={mfl_api_key}&FRANCHISE=&W=&JSON=1"
    response = requests.get(url)
    response.raise_for_status()
    yield response.json()

@dlt.source
def rosters_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    load_info = create_dlt_pipeline(
        pipeline_name='mfl_rosters',
        dataset_name='rosters',
        resource_func=rosters_resource,
        source_func=rosters_source,
        force_create_mode=force_create
    )
    print(load_info)

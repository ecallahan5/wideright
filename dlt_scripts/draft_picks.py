import os
import dlt
from dlt.sources.helpers import requests
from .common import _create_auth_headers, create_dlt_pipeline
from global_vars import host, league_id, league_year


@dlt.resource(write_disposition="replace")
def draft_picks_resource(mfl_api_key=dlt.secrets.value):
    # headers = _create_auth_headers(mfl_api_key) # Not used by MFL API if key is in URL
    # print(headers)

    # make an api call here
    url = f"https://{host}/{league_year}/export?TYPE=futureDraftPicks&L={league_id}&APIKEY={mfl_api_key}&JSON=1"
    response = requests.get(url)
    response.raise_for_status()
    yield response.json()

@dlt.source
def draft_picks_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    create_dlt_pipeline(
        pipeline_name='mfl_draft_picks',
        dataset_name='draft_picks',
        resource_func=draft_picks_resource,
        source_func=draft_picks_source,
        force_create_mode=force_create
    )

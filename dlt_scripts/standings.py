import os
import dlt
from dlt.sources.helpers import requests
from .common import create_dlt_pipeline
from global_vars import host, league_id, league_year


@dlt.resource(write_disposition="replace")
def standings_resource(mfl_api_key=dlt.secrets.value):
    # make an api call here
    url = f"https://{host}/{league_year}/export?TYPE=leagueStandings&L={league_id}&APIKEY={mfl_api_key}&COLUMN_NAMES=&ALL=&WEB=&JSON=1"
    response = requests.get(url)
    response.raise_for_status()
    yield response.json()

@dlt.source
def standings_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    create_dlt_pipeline(
        pipeline_name='mfl_standings',
        dataset_name='standings',
        resource_func=standings_resource,
        source_func=standings_source,
        force_create_mode=force_create

    )

import dlt
from dlt.sources.helpers import requests
from .common import _create_auth_headers, create_dlt_pipeline
from global_vars import host, league_id, league_year, last_league_year


@dlt.resource(write_disposition="replace")
def sourcename_resource(mfl_api_key=dlt.secrets.value):
    headers = _create_auth_headers(mfl_api_key)

    # check if authentication headers look fine
    print(headers)

    # make an api call here
    url = f"https://{host}/{last_league_year}/export?TYPE=playerScores&L={league_id}&APIKEY={mfl_api_key}&W=YTD&YEAR=&PLAYERS=&POSITION=&STATUS=&RULES=&COUNT=&JSON=1"
    response = requests.get(url)
    response.raise_for_status()
    yield response.json()

@dlt.source
def sourcename_source(sourcename_resource_func=dlt.secrets.value):
    yield sourcename_resource_func


if __name__ == "__main__":
    create_dlt_pipeline(
        pipeline_name='mfl_last_yr_scores',
        dataset_name='last_yr_scores',
        resource_func=sourcename_resource,
        source_func=sourcename_source
    )

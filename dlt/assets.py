import dlt
from dlt.sources.helpers import requests
import config


@dlt.source
def sourcename_source(api_secret_key=dlt.secrets.value):
    return sourcename_resource(api_secret_key)


def _create_auth_headers(api_secret_key):
    """Constructs Bearer type authorization header which is the most common authorization method"""
    headers = {"Authorization": f"Bearer {api_secret_key}"}
    return headers


@dlt.resource(write_disposition="replace")
def sourcename_resource(api_secret_key=dlt.secrets.value):
    headers = _create_auth_headers(api_secret_key)

    # check if authentication headers look fine
    print(headers)

    # make an api call here
    url = f"https://www49.myfantasyleague.com/{config.league_year}/export?TYPE=assets&L={config.league_id}&APIKEY={config.mfl_api_key}&JSON=1"
    response = requests.get(url)
    response.raise_for_status()
    yield response.json()


if __name__ == "__main__":
    # configure the pipeline with your destination details
    pipeline = dlt.pipeline(
        pipeline_name='mfl_assets', destination='bigquery', dataset_name='assets'
    )

    # print credentials by running the resource
    data = list(sourcename_resource())

    # run the pipeline with your parameters
    load_info = pipeline.run(sourcename_source())

    # pretty print the information on data that was loaded
    print(load_info)

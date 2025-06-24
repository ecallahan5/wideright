import dlt
from dlt.sources.helpers import requests
from .common import _create_auth_headers, create_dlt_pipeline
from global_vars import host, league_id, league_year


@dlt.resource(write_disposition="replace")
def assets_resource(mfl_api_key=dlt.secrets.value):
    # headers = _create_auth_headers(mfl_api_key) # Not used by MFL API if key is in URL
    # print(headers)

    print(f"[assets_resource] Entered. MFL API Key (from dlt.secrets.value) starts with: {str(mfl_api_key)[:5]}..." if mfl_api_key and len(str(mfl_api_key)) > 5 else "[assets_resource] MFL API Key from dlt.secrets.value is short or not set.")

    # make an api call here
    print(f"[assets_resource] Requesting URL: https://{host}/{league_year}/export?TYPE=assets&L={league_id}&APIKEY=MASKED_FOR_LOG&JSON=1")
    url = f"https://{host}/{league_year}/export?TYPE=assets&L={league_id}&APIKEY={mfl_api_key}&JSON=1"
    try:
        response = requests.get(url, timeout=30) # Added timeout
        response.raise_for_status()
        print("[assets_resource] API request successful.")
        yield response.json()
    except requests.exceptions.RequestException as e:
        print(f"[assets_resource] API request failed: {e}")
        raise # Re-raise the exception to be caught by the main block or DLT

@dlt.source
def assets_source(resource_func): # Changed argument name to be generic like others
    print("[assets_source] Entered, yielding resource_func.")
    yield resource_func


if __name__ == "__main__":
    print("[assets.py] Running script in __main__ block...")
    load_info = None # Initialize load_info
    try:
        print("[assets.py] Calling create_dlt_pipeline for mfl_assets...")
        # configure the pipeline with your destination details
        # Transformed data will be loaded to BigQuery tables with names matching the resource names
        load_info = create_dlt_pipeline(
            pipeline_name='mfl_assets',
            dataset_name='assets',
            resource_func=assets_resource, # Use the renamed resource
            source_func=assets_source # Use the renamed source
        )
        print("[assets.py] create_dlt_pipeline call finished.")
    except Exception as e:
        print(f"[assets.py] An error occurred during DLT pipeline execution: {e}")
        import traceback
        traceback.print_exc() # Print full traceback
    finally:
        print(f"[assets.py] Load info: {load_info}")
        print("[assets.py] Script finished.")

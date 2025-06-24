import dlt
from dlt.sources.helpers import requests
from .common import _create_auth_headers, create_dlt_pipeline
from global_vars import host, league_id, league_year


@dlt.resource(write_disposition="replace")
def assets_resource(mfl_api_key=dlt.secrets.value):
    # headers = _create_auth_headers(mfl_api_key) # Not used by MFL API if key is in URL
    # print(headers)

    # Log the league_year being used for this resource call
    print(f"[assets_resource] Using league_year from global_vars: {league_year}")
    print(f"[assets_resource] Entered. MFL API Key (from dlt.secrets.value) starts with: {str(mfl_api_key)[:5]}..." if mfl_api_key and len(str(mfl_api_key)) > 5 else "[assets_resource] MFL API Key from dlt.secrets.value is short or not set.")

    # make an api call here
    print(f"[assets_resource] Requesting URL: https://{host}/{league_year}/export?TYPE=assets&L={league_id}&APIKEY=MASKED_FOR_LOG&JSON=1")
    url = f"https://{host}/{league_year}/export?TYPE=assets&L={league_id}&APIKEY={mfl_api_key}&JSON=1"
    try:
        response = requests.get(url, timeout=30) # Added timeout
        response.raise_for_status()
        print("[assets_resource] API request successful.")

        api_data = response.json()
        print(f"[assets_resource] API response type: {type(api_data)}")

        if isinstance(api_data, dict):
            print(f"[assets_resource] API response top-level keys: {list(api_data.keys())}")
            # Log the 'error' field if it exists
            if 'error' in api_data:
                print(f"[assets_resource] API Error field content: {api_data.get('error')}")

            # Inspect common MFL structure for assets, e.g. response -> assets -> asset list
            assets_outer_dict = api_data.get('assets')
            if isinstance(assets_outer_dict, dict):
                print(f"[assets_resource] 'assets' field is a dict. Keys: {list(assets_outer_dict.keys())}")
                asset_list_or_dict = assets_outer_dict.get('asset')
                if isinstance(asset_list_or_dict, list):
                    print(f"[assets_resource] 'assets.asset' is a list. Length: {len(asset_list_or_dict)}")
                    if len(asset_list_or_dict) > 0 and isinstance(asset_list_or_dict[0], dict):
                        print(f"[assets_resource] First item in 'assets.asset' list has keys: {list(asset_list_or_dict[0].keys())}")
                elif isinstance(asset_list_or_dict, dict):
                     print(f"[assets_resource] 'assets.asset' is a dict. Keys: {list(asset_list_or_dict.keys())}")
                elif asset_list_or_dict is None:
                    print("[assets_resource] 'assets.asset' field is None.")
                else:
                    print(f"[assets_resource] 'assets.asset' field is of unexpected type: {type(asset_list_or_dict)}")
            elif assets_outer_dict is None:
                print("[assets_resource] 'assets' field is None in API response.") # This was hit in previous log
            else:
                print(f"[assets_resource] 'assets' field is of unexpected type: {type(assets_outer_dict)}")

        elif isinstance(api_data, list):
            print(f"[assets_resource] API response is a list. Length: {len(api_data)}")
            if len(api_data) > 0 and isinstance(api_data[0], dict):
                 print(f"[assets_resource] First item in API response list has keys: {list(api_data[0].keys())}")

        yield api_data

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

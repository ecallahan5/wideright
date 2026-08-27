import dlt
from dlt.sources.helpers import requests
from global_vars import host, league_id, league_year

def fetch_mfl_data(api_type, mfl_api_key, extra_params=""):
    """Centralized helper to query the MFL API with standard timeout and error handling."""
    # Read MFL_USER_ID from environment variable or dlt secrets
    import os
    mfl_user_id = os.getenv("MFL_USER_ID") or dlt.secrets.get("mfl_user_id")
    cookies = {}
    if mfl_user_id:
        cookies["MFL_USER_ID"] = mfl_user_id
        # Only the assets endpoint rejects requests that carry both the
        # cookie and the APIKEY at once. Every other endpoint needs the
        # APIKEY present even when the cookie is set, so only clear it here.
        if api_type == "assets":
            mfl_api_key = ""

    url = f"https://{host}/{league_year}/export?TYPE={api_type}&L={league_id}&APIKEY={mfl_api_key}&JSON=1{extra_params}"
    response = requests.get(url, cookies=cookies, timeout=30)
    response.raise_for_status()
    data = response.json()

    # MFL can return a 200 with an error payload instead of real data
    # (e.g. bad/missing auth). Without this check that error object gets
    # silently loaded into BigQuery as if it were valid data.
    if isinstance(data, dict) and "error" in data:
        raise ValueError(f"MFL API error for TYPE={api_type}: {data['error']}")

    return data

def create_dlt_pipeline(pipeline_name, dataset_name, resource_func, source_func, write_disposition=None, force_create_mode=False):
    """Creates and runs a DLT pipeline.
    """
    
    pipeline_obj = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination='bigquery',
        dataset_name=dataset_name
    )

    run_options = {}
    effective_write_disposition = "replace"

    if force_create_mode:
        print(f"Pipeline '{pipeline_name}': force_create_mode is True. Using 'replace' disposition and 'drop_sources' refresh mode.")
        run_options["refresh"] = "drop_sources"
    
    run_options["write_disposition"] = effective_write_disposition
    
    print(f"Running pipeline '{pipeline_name}' with options: {run_options}")

    try:
        # Apply the resource_func to the source_func before passing to pipeline.run
        load_info = pipeline_obj.run(source_func(resource_func), **run_options)
        print(f"Pipeline '{pipeline_name}' completed successfully with options: {run_options}")
        print(load_info)
        return load_info
    except Exception as e:
        print(f"An error occurred during pipeline '{pipeline_name}' run with options {run_options}: {e}")
        raise

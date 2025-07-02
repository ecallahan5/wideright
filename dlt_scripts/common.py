import dlt
from dlt.sources.helpers import requests
# from dlt.destinations.exceptions import DatabaseUndefinedRelation # Not needed for this simpler logic

def _create_auth_headers(api_secret_key):
    """Constructs Bearer type authorization header which is the most common authorization method"""
    headers = {"Authorization": f"Bearer {api_secret_key}"}
    return headers

def create_dlt_pipeline(pipeline_name, dataset_name, resource_func, source_func, write_disposition=None):
    """Creates and runs a DLT pipeline.
    Defaults to 'append' if write_disposition is None, which should create tables if they don't exist.
    If 'replace' is specified, it will be used directly.
    """

    effective_write_disposition = write_disposition if write_disposition is not None else "append"

    print(f"Running pipeline '{pipeline_name}' with effective_write_disposition: {effective_write_disposition}")

    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination='bigquery',
        dataset_name=dataset_name
    )

    try:
        # Apply the resource_func to the source_func before passing to pipeline.run
        load_info = pipeline.run(source_func(resource_func), write_disposition=effective_write_disposition)
        print(f"Pipeline '{pipeline_name}' completed successfully with {effective_write_disposition}.")
        print(load_info)
        return load_info
    except Exception as e:
        print(f"An error occurred during pipeline '{pipeline_name}' run with {effective_write_disposition}: {e}")
        # This will catch any error, including credential errors or actual BigQuery errors.
        # If 'append' fails to create a table, the error message from BigQuery/dlt should indicate why.
        # If 'replace' fails (e.g., table not found for truncate), this will also be caught.
        raise

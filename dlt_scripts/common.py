import dlt
from dlt.sources.helpers import requests

def _create_auth_headers(api_secret_key):
    """Constructs Bearer type authorization header which is the most common authorization method"""
    headers = {"Authorization": f"Bearer {api_secret_key}"}
    return headers

def create_dlt_pipeline(pipeline_name, dataset_name, resource_func, source_func, write_disposition=None):
    """Creates and runs a DLT pipeline."""
    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination='bigquery',
        dataset_name=dataset_name
    )
    # Apply the resource_func to the source_func before passing to pipeline.run
    if write_disposition:
        load_info = pipeline.run(source_func(resource_func), write_disposition=write_disposition)
    else:
        load_info = pipeline.run(source_func(resource_func))
    print(load_info)

    return load_info

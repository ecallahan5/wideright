import dlt
from dlt.sources.helpers import requests

def create_dlt_pipeline(pipeline_name, dataset_name, resource_func, source_func, write_disposition=None, force_create_mode=False):
    """Creates and runs a DLT pipeline.
    """
    
    pipeline_obj = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination='bigquery',
        dataset_name=dataset_name
    )

    run_options = {}

    if force_create_mode:
        print(f"Pipeline '{pipeline_name}': force_create_mode is True. Using 'replace' disposition and 'drop_sources' refresh mode.")
        run_options["refresh"] = "drop_sources"
        effective_write_disposition = "replace"
    else:
        effective_write_disposition = write_disposition or "replace"

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

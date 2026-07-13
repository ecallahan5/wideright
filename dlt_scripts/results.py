import os
import dlt
from .common import create_dlt_pipeline, fetch_mfl_data


@dlt.resource(write_disposition="replace")
def results_resource(mfl_api_key=dlt.secrets.value):
    yield fetch_mfl_data("weeklyResults", mfl_api_key, "&W=YTD&MISSING_AS_BYE=")

@dlt.source
def results_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    create_dlt_pipeline(
        pipeline_name='mfl_results',
        dataset_name='results',
        resource_func=results_resource,
        source_func=results_source,
        force_create_mode=force_create

    )

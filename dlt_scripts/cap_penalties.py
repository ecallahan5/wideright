import os
import dlt
from .common import create_dlt_pipeline, fetch_mfl_data


@dlt.resource(write_disposition="replace")
def league_resource(mfl_api_key=dlt.secrets.value):
    yield fetch_mfl_data("salaryAdjustments", mfl_api_key)

@dlt.source
def league_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    create_dlt_pipeline(
        pipeline_name='mfl_cap_penalties',
        dataset_name='cap_penalties',
        resource_func=league_resource,
        source_func=league_source,
        force_create_mode=force_create

    )

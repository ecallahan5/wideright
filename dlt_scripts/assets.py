import os
import dlt
from .common import create_dlt_pipeline, fetch_mfl_data


@dlt.resource(write_disposition="replace")
def assets_resource(mfl_api_key=dlt.secrets.value):
    yield fetch_mfl_data("assets", mfl_api_key)

@dlt.source
def assets_source(resource_func): # Changed argument name to be generic like others
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    create_dlt_pipeline(
        pipeline_name='mfl_assets',
        dataset_name='assets',
        resource_func=assets_resource,
        source_func=assets_source,
        force_create_mode=force_create )


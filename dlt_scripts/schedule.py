import os
import dlt
from .common import create_dlt_pipeline, fetch_mfl_data


@dlt.resource(write_disposition="replace")
def schedule_resource(mfl_api_key=dlt.secrets.value):
    yield fetch_mfl_data("schedule", mfl_api_key, "&W=&F=")

@dlt.source
def schedule_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    create_dlt_pipeline(
        pipeline_name='mfl_schedule',
        dataset_name='schedule',
        resource_func=schedule_resource,
        source_func=schedule_source,
        force_create_mode=force_create

    )

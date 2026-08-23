import os
import dlt
from .common import create_dlt_pipeline, fetch_mfl_data


@dlt.resource(write_disposition="replace")
def rosters_resource(mfl_api_key=dlt.secrets.value):
    yield fetch_mfl_data("rosters", mfl_api_key, "&FRANCHISE=&W=")["rosters"]["franchise"]

@dlt.source
def rosters_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    load_info = create_dlt_pipeline(
        pipeline_name='mfl_rosters',
        dataset_name='rosters',
        resource_func=rosters_resource,
        source_func=rosters_source,
        force_create_mode=force_create

    )
    print(load_info)

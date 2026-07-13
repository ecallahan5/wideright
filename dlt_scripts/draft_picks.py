import os
import dlt
from .common import create_dlt_pipeline, fetch_mfl_data


@dlt.resource(write_disposition="replace")
def draft_picks_resource(mfl_api_key=dlt.secrets.value):
    yield fetch_mfl_data("futureDraftPicks", mfl_api_key)

@dlt.source
def draft_picks_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    create_dlt_pipeline(
        pipeline_name='mfl_draft_picks',
        dataset_name='draft_picks',
        resource_func=draft_picks_resource,
        source_func=draft_picks_source,
        force_create_mode=force_create

    )

import os
import dlt
from .common import create_dlt_pipeline, fetch_mfl_data


@dlt.resource(write_disposition="replace")
def players_resource(mfl_api_key=dlt.secrets.value):
    yield fetch_mfl_data("players", mfl_api_key, "&DETAILS=&SINCE=&PLAYERS=")["players"]["player"]

@dlt.source
def players_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    create_dlt_pipeline(
        pipeline_name='mfl_players',
        dataset_name='players',
        resource_func=players_resource,
        source_func=players_source,
        force_create_mode=force_create

    )

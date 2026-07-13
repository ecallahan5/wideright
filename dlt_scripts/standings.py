import os
import dlt
from .common import create_dlt_pipeline, fetch_mfl_data


@dlt.resource(write_disposition="replace")
def standings_resource(mfl_api_key=dlt.secrets.value):
    yield fetch_mfl_data("leagueStandings", mfl_api_key, "&COLUMN_NAMES=&ALL=&WEB=")

@dlt.source
def standings_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    create_dlt_pipeline(
        pipeline_name='mfl_standings',
        dataset_name='standings',
        resource_func=standings_resource,
        source_func=standings_source,
        force_create_mode=force_create

    )

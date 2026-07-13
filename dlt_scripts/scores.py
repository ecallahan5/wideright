import os
import dlt
from .common import create_dlt_pipeline, fetch_mfl_data


@dlt.resource(write_disposition="replace")
def scores_resource(mfl_api_key=dlt.secrets.value):
    yield fetch_mfl_data("playerScores", mfl_api_key, "&W=YTD&YEAR=&PLAYERS=&POSITION=&STATUS=&RULES=&COUNT=")

@dlt.source
def scores_source(resource_func):
    yield resource_func


if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    create_dlt_pipeline(
        pipeline_name='mfl_scores',
        dataset_name='scores',
        resource_func=scores_resource,
        source_func=scores_source,
        force_create_mode=force_create

    )

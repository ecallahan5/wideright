from . import common # Use relative import for common
from .common import config # Make config available for config.last_league_year

# Define the specific resource for last year's scores
def last_yr_scores_resource():
    # Pass the specific year and W parameter to create_dlt_resource
    # Other parameters like PLAYERS, POSITION etc. were empty in the original URL,
    # so they will default to "" in make_api_call.
    return common.create_dlt_resource(type_name="playerScores", year=config.last_league_year, w="YTD")


# Define the specific source for last year's scores
def last_yr_scores_source():
    return common.create_dlt_source(last_yr_scores_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_last_yr_scores'
    dataset_name = 'last_yr_scores'

    print("Listing data from resource for debugging (as in original script):")
    data = list(last_yr_scores_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=last_yr_scores_source,
        resource_func_to_pass_to_source=last_yr_scores_resource
    )

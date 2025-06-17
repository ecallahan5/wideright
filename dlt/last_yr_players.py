from . import common # Use relative import for common
from .common import config # Make config available for config.last_league_year

# Define the specific resource for last year's players
def last_yr_players_resource():
    # Pass the specific year to create_dlt_resource
    return common.create_dlt_resource(type_name="players", year=config.last_league_year, details="", since="", players="")


# Define the specific source for last year's players
def last_yr_players_source():
    return common.create_dlt_source(last_yr_players_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_last_yr_players'
    dataset_name = 'last_yr_players'

    print("Listing data from resource for debugging (as in original script):")
    data = list(last_yr_players_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=last_yr_players_source,
        resource_func_to_pass_to_source=last_yr_players_resource
    )

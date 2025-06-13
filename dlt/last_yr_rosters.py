from . import common # Use relative import for common
from .common import config # Make config available for config.last_league_year

# Define the specific resource for last year's rosters
def last_yr_rosters_resource():
    # Pass the specific year to create_dlt_resource
    # The original URL had FRANCHISE=&W= which are empty.
    return common.create_dlt_resource(type_name="rosters", year=config.last_league_year, franchise="", w="")


# Define the specific source for last year's rosters
def last_yr_rosters_source():
    return common.create_dlt_source(last_yr_rosters_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_last_yr_rosters'
    dataset_name = 'last_yr_rosters'

    print("Listing data from resource for debugging (as in original script):")
    data = list(last_yr_rosters_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=last_yr_rosters_source,
        resource_func_to_pass_to_source=last_yr_rosters_resource
    )

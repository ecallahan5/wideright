from . import common # Use relative import for common

# Define the specific resource for league
def league_resource():
    # year defaults to config.league_year in create_dlt_resource
    return common.create_dlt_resource(type_name="league")

# Define the specific source for league
def league_source():
    return common.create_dlt_source(league_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_league'
    dataset_name = 'league'

    print("Listing data from resource for debugging (as in original script):")
    data = list(league_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=league_source,
        resource_func_to_pass_to_source=league_resource
    )

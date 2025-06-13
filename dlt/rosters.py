from . import common # Use relative import for common

# Define the specific resource for rosters
def rosters_resource():
    # year defaults to config.league_year in create_dlt_resource
    # The original URL had FRANCHISE=&W= which are empty.
    # Pass them as empty strings to make_api_call.
    return common.create_dlt_resource(type_name="rosters", franchise="", w="")


# Define the specific source for rosters
def rosters_source():
    return common.create_dlt_source(rosters_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_rosters'
    dataset_name = 'rosters'

    print("Listing data from resource for debugging (as in original script):")
    data = list(rosters_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=rosters_source,
        resource_func_to_pass_to_source=rosters_resource
    )

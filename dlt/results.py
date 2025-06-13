from . import common # Use relative import for common

# Define the specific resource for results
def results_resource():
    # year defaults to config.league_year in create_dlt_resource
    # The original URL had W=YTD and an empty MISSING_AS_BYE.
    return common.create_dlt_resource(type_name="weeklyResults", w="YTD") # MISSING_AS_BYE defaults to ""

# Define the specific source for results
def results_source():
    return common.create_dlt_source(results_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_results'
    dataset_name = 'results'

    print("Listing data from resource for debugging (as in original script):")
    data = list(results_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=results_source,
        resource_func_to_pass_to_source=results_resource
    )

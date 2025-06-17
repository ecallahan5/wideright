from . import common # Use relative import for common

# Define the specific resource for scores
def scores_resource():
    # year defaults to config.league_year in create_dlt_resource
    # Other parameters like PLAYERS, POSITION etc. were empty in the original URL,
    # so they will default to "" in make_api_call.
    return common.create_dlt_resource(type_name="playerScores", w="YTD")


# Define the specific source for scores
def scores_source():
    return common.create_dlt_source(scores_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_scores'
    dataset_name = 'scores'

    print("Listing data from resource for debugging (as in original script):")
    data = list(scores_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=scores_source,
        resource_func_to_pass_to_source=scores_resource
    )

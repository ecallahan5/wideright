
from . import common # Use relative import for common

# Define the specific resource for draft picks
def draft_picks_resource():
    # year defaults to config.league_year in create_dlt_resource
    return common.create_dlt_resource(type_name="futureDraftPicks")

# Define the specific source for draft picks
def draft_picks_source():
    return common.create_dlt_source(draft_picks_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_draft_picks'
    dataset_name = 'draft_picks'
    
    print("Listing data from resource for debugging (as in original script):")
    data = list(draft_picks_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=draft_picks_source,
        resource_func_to_pass_to_source=draft_picks_resource
    )
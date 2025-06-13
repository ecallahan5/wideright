from . import common # Use relative import for common

# Define the specific resource for standings
def standings_resource():
    # year defaults to config.league_year in create_dlt_resource
    # Extra params like COLUMN_NAMES, ALL, WEB were empty in original URL, will default to ""
    return common.create_dlt_resource(type_name="leagueStandings")

# Define the specific source for standings
def standings_source():
    return common.create_dlt_source(standings_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_standings'
    dataset_name = 'standings'

    print("Listing data from resource for debugging (as in original script):")
    data = list(standings_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=standings_source,
        resource_func_to_pass_to_source=standings_resource
    )

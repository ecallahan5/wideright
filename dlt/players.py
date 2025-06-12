from . import common # Use relative import for common

# Define the specific resource for players
def players_resource():
    # year defaults to config.league_year in create_dlt_resource
    # The original URL had DETAILS=&SINCE=&PLAYERS= which are empty.
    # Pass them as empty strings to make_api_call.
    return common.create_dlt_resource(type_name="players", details="", since="", players="")

# Define the specific source for players
def players_source():
    return common.create_dlt_source(players_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_players'
    dataset_name = 'players'

    print("Listing data from resource for debugging (as in original script):")
    data = list(players_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=players_source,
        resource_func_to_pass_to_source=players_resource
    )

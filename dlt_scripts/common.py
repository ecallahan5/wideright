import dlt
from dlt.sources.helpers import requests
from global_vars import host, league_id, league_year, last_league_year

# Central registry of MFL API endpoints and their configurations.
# Keys represent the dataset names, which also match the script/resource names.
PIPELINE_CONFIGS = {
    "assets": {
        "api_type": "assets",
        "extra_params": "",
        "use_last_year": False,
        "pipeline_name": "mfl_assets"
    },
    "cap_penalties": {
        "api_type": "salaryAdjustments",
        "extra_params": "",
        "use_last_year": False,
        "pipeline_name": "mfl_cap_penalties"
    },
    "draft_picks": {
        "api_type": "futureDraftPicks",
        "extra_params": "",
        "use_last_year": False,
        "pipeline_name": "mfl_draft_picks"
    },
    "league": {
        "api_type": "league",
        "extra_params": "",
        "use_last_year": False,
        "pipeline_name": "mfl_league"
    },
    "players": {
        "api_type": "players",
        "extra_params": "&DETAILS=&SINCE=&PLAYERS=",
        "use_last_year": False,
        "pipeline_name": "mfl_players"
    },
    "results": {
        "api_type": "weeklyResults",
        "extra_params": "&W=YTD&MISSING_AS_BYE=",
        "use_last_year": False,
        "pipeline_name": "mfl_results"
    },
    "rosters": {
        "api_type": "rosters",
        "extra_params": "&FRANCHISE=&W=",
        "use_last_year": False,
        "pipeline_name": "mfl_rosters"
    },
    "schedule": {
        "api_type": "schedule",
        "extra_params": "&W=&F=",
        "use_last_year": False,
        "pipeline_name": "mfl_schedule"
    },
    "scores": {
        "api_type": "playerScores",
        "extra_params": "&W=YTD&YEAR=&PLAYERS=&POSITION=&STATUS=&RULES=&COUNT=",
        "use_last_year": False,
        "pipeline_name": "mfl_scores"
    },
    "standings": {
        "api_type": "leagueStandings",
        "extra_params": "&COLUMN_NAMES=&ALL=&WEB=",
        "use_last_year": False,
        "pipeline_name": "mfl_standings"
    },
    "last_yr_players": {
        "api_type": "players",
        "extra_params": "&DETAILS=&SINCE=&PLAYERS=",
        "use_last_year": True,
        "pipeline_name": "mfl_last_yr_players"
    },
    "last_yr_rosters": {
        "api_type": "rosters",
        "extra_params": "&FRANCHISE=&W=",
        "use_last_year": True,
        "pipeline_name": "mfl_last_yr_rosters"
    },
    "last_yr_scores": {
        "api_type": "playerScores",
        "extra_params": "&W=YTD&YEAR=&PLAYERS=&POSITION=&STATUS=&RULES=&COUNT=",
        "use_last_year": True,
        "pipeline_name": "mfl_last_yr_scores"
    }
}

def fetch_mfl_data(api_type, mfl_api_key, extra_params="", year=None):
    """Centralized helper to query the MFL API with standard timeout and error handling."""
    query_year = year or league_year
    url = f"https://{host}/{query_year}/export?TYPE={api_type}&L={league_id}&APIKEY={mfl_api_key}&JSON=1{extra_params}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()

def get_resource_by_name(name):
    """Dynamically generates a decorated DLT resource function based on config."""
    if name not in PIPELINE_CONFIGS:
        raise ValueError(f"Unknown pipeline name: {name}")
    
    cfg = PIPELINE_CONFIGS[name]
    api_type = cfg["api_type"]
    extra_params = cfg["extra_params"]
    use_last_year = cfg["use_last_year"]
    
    # We define the inner function and apply dlt.resource.
    # We set the resource name dynamically.
    @dlt.resource(name=name, write_disposition="replace")
    def resource_func(mfl_api_key=dlt.secrets.value):
        year = last_league_year if use_last_year else league_year
        yield fetch_mfl_data(api_type, mfl_api_key, extra_params, year=year)
        
    return resource_func

def create_dlt_pipeline(pipeline_name, dataset_name, resource_func, source_func=None, write_disposition=None, force_create_mode=False):
    """Creates and runs a DLT pipeline."""
    pipeline_obj = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination='bigquery',
        dataset_name=dataset_name
    )

    run_options = {}
    effective_write_disposition = "replace"

    if force_create_mode:
        print(f"Pipeline '{pipeline_name}': force_create_mode is True. Using 'replace' disposition and 'drop_sources' refresh mode.")
        run_options["refresh"] = "drop_sources"
    
    run_options["write_disposition"] = effective_write_disposition
    
    print(f"Running pipeline '{pipeline_name}' with options: {run_options}")

    try:
        # If source_func is provided, use it to wrap resource_func; otherwise run resource directly
        data_to_load = source_func(resource_func) if source_func is not None else resource_func()
        load_info = pipeline_obj.run(data_to_load, **run_options)
        print(f"Pipeline '{pipeline_name}' completed successfully with options: {run_options}")
        print(load_info)
        return load_info
    except Exception as e:
        print(f"An error occurred during pipeline '{pipeline_name}' run with options {run_options}: {e}")
        raise

def run_pipeline_by_name(name, force_create_mode=False):
    """Orchestrates the running of a single pipeline by its registry name."""
    if name not in PIPELINE_CONFIGS:
        raise ValueError(f"Unknown pipeline: {name}")
    
    cfg = PIPELINE_CONFIGS[name]
    resource = get_resource_by_name(name)
    
    return create_dlt_pipeline(
        pipeline_name=cfg["pipeline_name"],
        dataset_name=name,
        resource_func=resource,
        source_func=None,
        force_create_mode=force_create_mode
    )


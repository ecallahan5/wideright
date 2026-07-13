import os
import dlt

from dlt_scripts.common import create_dlt_pipeline
from dlt_scripts.league import league_resource, league_source
from dlt_scripts.draft_picks import draft_picks_resource, draft_picks_source
from dlt_scripts.players import players_resource, players_source
from dlt_scripts.rosters import rosters_resource, rosters_source
from dlt_scripts.assets import assets_resource, assets_source
from dlt_scripts.schedule import schedule_resource, schedule_source
from dlt_scripts.scores import scores_resource, scores_source
from dlt_scripts.standings import standings_resource, standings_source
from dlt_scripts.results import results_resource, results_source
from dlt_scripts.cap_penalties import league_resource as cap_penalties_resource, league_source as cap_penalties_source

def run_pipelines():
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    
    print("--- Starting DLT Pipeline Runs ---")
    
    # 1. League metadata
    create_dlt_pipeline(
        pipeline_name='mfl_league',
        dataset_name='league',
        resource_func=league_resource,
        source_func=league_source,
        force_create_mode=force_create
    )
    
    # 2. Draft Picks
    create_dlt_pipeline(
        pipeline_name='mfl_draft_picks',
        dataset_name='draft_picks',
        resource_func=draft_picks_resource,
        source_func=draft_picks_source,
        force_create_mode=force_create
    )
    
    # 3. Players
    create_dlt_pipeline(
        pipeline_name='mfl_players',
        dataset_name='players',
        resource_func=players_resource,
        source_func=players_source,
        force_create_mode=force_create
    )
    
    # 4. Rosters
    create_dlt_pipeline(
        pipeline_name='mfl_rosters',
        dataset_name='rosters',
        resource_func=rosters_resource,
        source_func=rosters_source,
        force_create_mode=force_create
    )
    
    # 5. Assets
    create_dlt_pipeline(
        pipeline_name='mfl_assets',
        dataset_name='assets',
        resource_func=assets_resource,
        source_func=assets_source,
        force_create_mode=force_create
    )
    
    # 6. Schedule
    create_dlt_pipeline(
        pipeline_name='mfl_schedule',
        dataset_name='schedule',
        resource_func=schedule_resource,
        source_func=schedule_source,
        force_create_mode=force_create
    )
    
    # 7. Scores
    create_dlt_pipeline(
        pipeline_name='mfl_scores',
        dataset_name='scores',
        resource_func=scores_resource,
        source_func=scores_source,
        force_create_mode=force_create
    )
    
    # 8. Standings
    create_dlt_pipeline(
        pipeline_name='mfl_standings',
        dataset_name='standings',
        resource_func=standings_resource,
        source_func=standings_source,
        force_create_mode=force_create
    )
    
    # 9. Results
    create_dlt_pipeline(
        pipeline_name='mfl_results',
        dataset_name='results',
        resource_func=results_resource,
        source_func=results_source,
        force_create_mode=force_create
    )
    
    # 10. Cap Penalties
    create_dlt_pipeline(
        pipeline_name='mfl_cap_penalties',
        dataset_name='cap_penalties',
        resource_func=cap_penalties_resource,
        source_func=cap_penalties_source,
        force_create_mode=force_create
    )
    
    print("--- Finished All DLT Pipeline Runs ---")

if __name__ == "__main__":
    run_pipelines()

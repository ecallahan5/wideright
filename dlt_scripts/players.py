import os
import dlt
from .common import run_pipeline_by_name, get_resource_by_name

# Retrieve the centralized resource function for backwards compatibility
players_resource = get_resource_by_name("players")

@dlt.source
def players_source(resource_func):
    yield resource_func

if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    run_pipeline_by_name("players", force_create_mode=force_create)

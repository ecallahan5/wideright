import os
import dlt
from .common import run_pipeline_by_name, get_resource_by_name

# Retrieve the centralized resource function for backwards compatibility
last_yr_rosters_resource = get_resource_by_name("last_yr_rosters")

@dlt.source
def last_yr_rosters_source(resource_func):
    yield resource_func

if __name__ == "__main__":
    force_create = os.getenv("FORCE_DLT_CREATE_MODE", "false").lower() == "true"
    run_pipeline_by_name("last_yr_rosters", force_create_mode=force_create)

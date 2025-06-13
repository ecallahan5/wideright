from . import common # Use relative import for common

# Define the specific resource for schedule
def schedule_resource():
    # year defaults to config.league_year in create_dlt_resource
    # The original URL had TYPE=schedule, W=, and F=.
    # F corresponds to the 'franchise' parameter in make_api_call.
    return common.create_dlt_resource(type_name="schedule", w="", franchise="")


# Define the specific source for schedule
def schedule_source():
    return common.create_dlt_source(schedule_resource)

if __name__ == "__main__":
    pipeline_name = 'mfl_schedule'
    dataset_name = 'schedule'

    print("Listing data from resource for debugging (as in original script):")
    data = list(schedule_resource())
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=schedule_source,
        resource_func_to_pass_to_source=schedule_resource
    )

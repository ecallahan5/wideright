
from . import common  # Use relative import for common
from .common import config # Make config available if it's used directly in main (though it shouldn't be for API calls now)

# Define the specific resource for assets
# common.create_dlt_resource will be decorated with @dlt.resource internally
def assets_resource():
    # year defaults to config.league_year in create_dlt_resource
    return common.create_dlt_resource(type_name="assets")


# Define the specific source for assets
# common.create_dlt_source will be decorated with @dlt.source internally
def assets_source():
    return common.create_dlt_source(assets_resource)

if __name__ == "__main__":
    # The pipeline name and dataset name from the original file
    pipeline_name = 'mfl_assets'
    dataset_name = 'assets'

    # Run the pipeline using the generalized function
    # common.run_pipeline will call assets_source, which in turn calls assets_resource.
    # assets_resource itself will be called by dlt when the source is iterated.

    # To replicate the original behavior of listing data first:
    print("Listing data from resource for debugging (as in original script):")
    # Note: assets_resource() directly gives the generator.
    # If common.create_dlt_resource is called directly, it also gives the generator.
    # The dlt framework handles the @dlt.resource and @dlt.source decorators.
    # For the list() call, we need to call the function that yields data.
    data = list(assets_resource()) # This will execute the resource function
    print(data)

    common.run_pipeline(
        pipeline_name=pipeline_name,
        dataset_name=dataset_name,
        source_func=assets_source, # Pass the source function
        resource_func_to_pass_to_source=assets_resource # Pass the resource function for the source to wrap
    )

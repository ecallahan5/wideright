import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (where config.py is)
parent_dir = os.path.dirname(script_dir)

# Add parent directory to sys.path for config.py
if parent_dir not in sys.path: # Avoid duplicate entries if already there
    sys.path.insert(0, parent_dir)
elif sys.path[0] != parent_dir: # If it's there but not at the start
    sys.path.remove(parent_dir)
    sys.path.insert(0, parent_dir)
# else: it's already at sys.path[0]

import config

# Remove parent_dir from sys.path to import the actual dlt library
# This assumes parent_dir was indeed added at sys.path[0] and is still there.
# A more robust pop would be to find and remove it if it exists.
# For now, stick to the plan's simpler pop(0) after confirming it was inserted at 0.
if sys.path[0] == parent_dir:
    sys.path.pop(0)
else:
    # Fallback: if parent_dir for some reason wasn't at index 0, try to remove it by value.
    # This case should ideally not be hit if the above insertion logic is correct.
    if parent_dir in sys.path:
        sys.path.remove(parent_dir)

# These imports should now find the installed 'dlt' library
import dlt
from dlt.sources.helpers import requests

# Add parent_dir back to sys.path to restore the original behavior for any subsequent local imports
# that might rely on it (though this is generally not ideal).
if parent_dir not in sys.path: # Avoid duplicate entries
    sys.path.insert(0, parent_dir)
elif sys.path[0] != parent_dir: # If it's there but not at the start
    sys.path.remove(parent_dir)
    sys.path.insert(0, parent_dir)


def make_api_call(type_name, year, api_key, host, league_id, details="", since="", players="", franchise="", w=""):
    """Makes an API call to the MFL server and returns the JSON response."""
    # Construct the base URL
    url = f"https://{host}/{year}/export?TYPE={type_name}&L={league_id}&APIKEY={api_key}"

    # Add optional parameters if they are provided
    if details:
        url += f"&DETAILS={details}"
    if since:
        url += f"&SINCE={since}"
    if players:
        url += f"&PLAYERS={players}"
    if franchise:
        url += f"&FRANCHISE={franchise}"
    if w:
        url += f"&W={w}"

    url += "&JSON=1"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()


@dlt.resource(write_disposition="replace")
def create_dlt_resource(type_name, year=None, api_key=dlt.secrets.value, details="", since="", players="", franchise="", w=""):
    """Creates a DLT resource that makes an API call and yields the JSON response."""
    if year is None:
        year = config.league_year

    # The MFL API key is passed directly from config, not as a dlt.secret
    # _create_auth_headers is not used by these MFL API calls
    # print(headers) # This was for debugging and can be removed

    data = make_api_call(
        type_name=type_name,
        year=year,
        api_key=config.mfl_api_key,  # Use the API key from config
        host=config.host,
        league_id=config.league_id,
        details=details,
        since=since,
        players=players,
        franchise=franchise,
        w=w
    )
    yield data


@dlt.source
def create_dlt_source(resource_func, api_secret_key=dlt.secrets.value): # api_secret_key is not used by MFL resources but kept for consistency with original code structure if needed elsewhere.
    """Creates a DLT source from a resource function."""
    # The api_secret_key parameter was part of the original sourcename_source,
    # but it's not actually used by the MFL API calls which use mfl_api_key from config.
    # We call resource_func without passing api_secret_key to it,
    # as create_dlt_resource doesn't expect it anymore for MFL calls.
    return resource_func


def run_pipeline(pipeline_name, dataset_name, source_func, resource_func_to_pass_to_source):
    """Runs a DLT pipeline and prints load information."""
    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination='bigquery',  # Assuming this is always the destination
        dataset_name=dataset_name
    )

    # The original code did: data = list(sourcename_resource())
    # This materializes all data from the resource before running the pipeline.
    # It's generally better to let the pipeline manage data streaming.
    # If pre-loading data is strictly necessary for debugging or other reasons,
    # it can be done, but for a standard pipeline run, it's not typical.
    # For now, I will replicate the original behavior of listing data first.
    # data = list(resource_func_to_pass_to_source()) # This line would need the resource_func with its specific parameters

    # The source_func (create_dlt_source) now expects the actual resource generating function.
    # And the resource function (create_dlt_resource) will be called by dlt internally.
    load_info = pipeline.run(source_func(resource_func_to_pass_to_source))

    print(f"Pipeline {pipeline_name} ran successfully.")
    print(load_info)

    # Example of how to list data from the source if needed for debugging,
    # but this should be done carefully as it consumes the generator.
    # print("Listing data from source for debugging:")
    # data_from_source = list(source_func(resource_func_to_pass_to_source()))
    # print(data_from_source)

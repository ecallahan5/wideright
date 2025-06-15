import os
import sys

# Determine project root directory more directly for clarity
# __file__ is dlt/common.py -> os.path.dirname(__file__) is dlt/
# os.path.dirname(os.path.dirname(__file__)) is project_root/
project_root_abs = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

original_path_zero = sys.path[0]
path_zero_was_empty_string = False
abs_path_was_also_in_sys_path = False # For restoring project_root_abs if it was removed separately

if original_path_zero == '':
    sys.path.pop(0)
    path_zero_was_empty_string = True
    # If '' was at path[0], current dir is project root.
    # Check if the absolute path to project root is ALSO in sys.path redundantly.
    if project_root_abs in sys.path:
        sys.path.remove(project_root_abs)
        abs_path_was_also_in_sys_path = True # Mark that we removed it by value
elif original_path_zero == project_root_abs: # Path[0] was the absolute project root
    sys.path.pop(0)
    # No need to set path_zero_was_empty_string, original_path_zero holds the value for restoration.
    # Check if '' is ALSO in sys.path redundantly.
    if '' in sys.path:
        sys.path.remove('')
        # We don't have a flag for this specific redundant '' removal, assume it's not critical to restore if abs path was primary.
elif project_root_abs in sys.path: # Project root was not at [0] but elsewhere
    sys.path.remove(project_root_abs)
    # original_path_zero is kept as is. Project root will be restored to index 0 in finally.
# else: project root is not in sys.path explicitly, assume standard lib / site-packages will be searched.

# Debug print before attempting dlt import
print(f"DEBUG: sys.path for dlt import: {sys.path}")

try:
    import dlt
    print(f"DEBUG: dlt imported from: {dlt.__file__}") # Debug print
    from dlt.sources.helpers import requests
    print(f"DEBUG: dlt.sources.helpers.requests imported: {requests.__file__}") # Debug print
finally:
    # Restore sys.path to a state that includes project root, preferably at index 0.
    # This logic aims to be safe rather than perfectly reversible if sys.path was unusually structured.

    # If path[0] was '' and we removed it:
    if path_zero_was_empty_string:
        if sys.path[0] != '': # If '' is not back at the start
            sys.path.insert(0, '')
    # Else if path[0] was project_root_abs and we removed it:
    elif original_path_zero == project_root_abs:
         if sys.path[0] != project_root_abs:
            sys.path.insert(0, project_root_abs)
    # Fallback: if project_root_abs (or '') is not in path[0], ensure one of them is.
    # Prefer '' if that was original, else project_root_abs.
    # This covers cases where project_root_abs was removed by value from a non-zero index.
    else:
        current_path_zero_is_root = (sys.path[0] == '' or sys.path[0] == project_root_abs)
        if not current_path_zero_is_root:
            # If original_path_zero was empty, prefer that, otherwise use abs.
            path_to_insert = '' if (original_path_zero == '' or path_zero_was_empty_string) else project_root_abs
            if path_to_insert not in sys.path: # Avoid adding if it's already there elsewhere
                sys.path.insert(0, path_to_insert)
            elif sys.path[0] != path_to_insert : # It's there, but not at [0]
                sys.path.remove(path_to_insert)
                sys.path.insert(0, path_to_insert)


    # If we specifically removed project_root_abs by value because it was redundant with '' at path[0]:
    if path_zero_was_empty_string and abs_path_was_also_in_sys_path:
        if project_root_abs not in sys.path: # And it's still not there
             # We choose not to re-add it if '' is already at path[0], as '' covers the project root.
             pass


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
        year = os.getenv("LEAGUE_YEAR")

    # The MFL API key is passed directly from config, not as a dlt.secret
    # _create_auth_headers is not used by these MFL API calls
    # print(headers) # This was for debugging and can be removed

    data = make_api_call(
        type_name=type_name,
        year=year, # year is already correctly sourced or passed
        api_key=os.getenv("MFL_API_KEY"),
        host=os.getenv("HOST"),
        league_id=os.getenv("LEAGUE_ID"),
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

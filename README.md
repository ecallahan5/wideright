# Wide Right Fantasy Football League Hub

Welcome to the Wide Right Fantasy Football League Hub! This is a Streamlit-based web application designed to help league members manage their teams, track league progress, and view various fantasy football data specific to our league.

## Key Features

This application provides a range of features, including:

*   **Dashboard:** A central hub (`🏠_Home.py`) to welcome users and display timely information.
*   **Roster Management:** View and manage team rosters.
*   **Player Data:** Access detailed player information and statistics.
*   **League Standings:** Track current league standings and division races.
*   **Transactions:** Manage and view trades, contract extensions, and taxi squad claims.
*   **Draft Center:** Information and tools related to rookie and free agent drafts, including future draft picks.
*   **Playoff Picture:** View projected standings and playoff probabilities.
*   **Points Race:** Track the league's points race.
*   **Payout Information:** Details on league payouts.
*   **Historical Data:** Access archived data from previous seasons (e.g., `2023 Archive`, `2024 Archive`).

## Project Structure

The repository is organized as follows:

*   `🏠_Home.py`: The main landing page for the Streamlit application.
*   **Yearly Archive Folders (e.g., `2023 Archive/`, `2024 Archive/`)**: These directories contain Streamlit pages specific to league activities for those years. In Streamlit, files in subdirectories are typically treated as modules for different pages or sections of the application.
*   `dlt/`: Contains Python scripts using the `dlt` (data load tool) library, likely for ingesting data from various sources (e.g., MFL API) into a data warehouse like Google BigQuery.
    *   `dlt/assets.py`: Likely defines dlt assets.
    *   `dlt/league.py`: Script to fetch general league data.
    *   Other files (`players.py`, `rosters.py`, etc.): Scripts for fetching specific data types.
*   `functions.py`: A collection of utility functions used throughout the application, such as fetching data from APIs, interacting with BigQuery, and data manipulation.
*   `global_vars.py`: Stores global variables, API endpoints, league-specific constants (like salary cap, contract years), and helper functions.
*   `.github/workflows/`: Contains GitHub Actions workflows for:
    *   Deploying the application to a server.
    *   Running scheduled tasks, such as updating MFL player data.
    *   Managing Streamlit upgrades.
*   `requirements.txt`: Lists the Python dependencies required to run the project.
*   `cache/`: Directory likely used for caching data, for example, by Streamlit's caching mechanisms or `dlt`.
*   `todos.txt`: A file listing pending tasks or future enhancements for the project.

## Setup and Usage

To run this application locally or contribute to its development, follow these steps:

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Set Up a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Credentials:**
    This application requires API keys and credentials for several services:
    *   **MyFantasyLeague (MFL):** API key for fetching league data.
    *   **wideright.app API:** A token for accessing custom league endpoints.
    *   **Google Cloud Platform (GCP):** Service account credentials (`.json` file) with access to BigQuery, Google Drive, and Google Sheets.

    These are typically managed through:
    *   **Streamlit Secrets:** For deployment, Streamlit Cloud allows you to store secrets securely. Locally, you would create a `.streamlit/secrets.toml` file. Refer to the [Streamlit documentation on Secrets Management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management) for more details.
    *   **`config.py` file:** Some scripts (especially in the `dlt` directory) might also expect a `config.py` file in the root directory containing sensitive information like API keys or host details.
        *   Ensure you have the necessary `config.py` file if you intend to run the `dlt` pipelines or scripts that import it.
        *   The `dlt/league.py` script, for example, imports `config` and uses `config.host`, `config.league_year`, `config.league_id`, and `config.mfl_api_key`.
        *   `functions.py` also imports `config` for `config.key` (site_token).

    **Example `secrets.toml` structure:**
    ```toml
    # .streamlit/secrets.toml
    [gcp_service_account]
    type = "service_account"
    project_id = "your-gcp-project-id"
    private_key_id = "your-private-key-id"
    private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
    client_email = "your-service-account-email@your-project-id.iam.gserviceaccount.com"
    client_id = "your-client-id"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account-email%40your-project-id.iam.gserviceaccount.com"

    # MFL API Key (if used directly by Streamlit pages, otherwise might be in config.py)
    # MFL_API_KEY = "your_mfl_api_key"

    # wideright.app API token (site_token)
    # WIDERIGHT_APP_TOKEN = "your_wideright_app_token"
    ```
    **Note:** The exact structure and required keys in `secrets.toml` and `config.py` will depend on how `st.secrets` and `config` are used throughout the application. You will need to acquire the correct keys and tokens for the league and services it connects to.

5.  **Run the Streamlit Application:**
    ```bash
    streamlit run 🏠_Home.py
    ```
    This will start the application, and you can access it via your web browser (usually at `http://localhost:8501`).

## Technologies Used

*   **Python:** The core programming language.
*   **Streamlit:** For building the interactive web application.
*   **Pandas:** For data manipulation and analysis.
*   **Requests:** For making HTTP requests to external APIs.
*   **MyFantasyLeague (MFL) API:** Source of fantasy football league data.
*   **Google BigQuery:** Used as a data warehouse, queried via `google-cloud-bigquery` library.
*   **dlt (data load tool):** For creating and managing data pipelines.
*   **GitHub Actions:** For CI/CD automation, including deployment and scheduled tasks.

## Data Sources and Management

This application relies heavily on data from the MyFantasyLeague (MFL) API for the specific league it serves (`L=59643` as seen in some API URLs) and potentially other custom data sources via the `wideright.app` API.

*   **Data Ingestion:** Scripts within the `dlt/` directory are responsible for fetching data from these sources and likely loading it into Google BigQuery.
*   **Data Caching:** Streamlit's caching mechanisms (`@st.cache_data`) are used in `functions.py` to improve performance by caching results from API calls and BigQuery queries. The `cache/` directory might also be used for storing cached data.
*   **Historical Data:** The presence of yearly archive folders (e.g., `2023 Archive/`, `2024 Archive/`) suggests that historical league data is maintained and accessible within the application.

## Future Enhancements & To-Do

This project is actively maintained, with ongoing plans for improvements and new features. Key areas for future development include:

*   **Code Refinement:** Ongoing Python code cleanup and optimization, such as standardizing variable usage (e.g., hostname) and centralizing calculations (e.g., week calculations in `global_vars.py`).
*   **Feature Enhancements:**
    *   Improvements to salary adjustment displays and extension validation (checking cap and contract year space).
    *   Automation of currently manual processes like tracking prizes and weekly pots.
*   **Technical Improvements:**
    *   Exploring webhook embeds.
    *   Investigating options for automatic cache clearing.

For a more detailed list of pending tasks and planned enhancements, please refer to the `todos.txt` file in this repository.

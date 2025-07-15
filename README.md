# PromptQL Thread Exporter

## Description

A CLI script to fetch thread data from the PromptQL API and output it as JSON, matching the structure in sample_thread_data.json.

## Installation

1. Ensure you have Python 3.8 or higher installed.
2. Install dependencies using pip:

   ```
   pip install -r requirements.txt
   ```

## Usage

You can now provide the API key in three ways (highest priority first):

1. **CLI flag**: `--api-key YOUR_API_KEY`
2. **Environment variable**: `API_KEY=YOUR_API_KEY`
3. **Config file**: As specified in your `~/.ddn/config.yaml` under `promptql_secret_keys`

Example usage:

```sh
python main.py --api-key YOUR_API_KEY --select thread1,thread2
```

If `--api-key` is not provided, the script will check the `API_KEY` environment variable. If neither is set, it will fall back to the config file.

- `--project-name`: The project name as found in your config.yaml (optional; if not provided, you will be prompted to select a project).
- `--project-id`: The full project key (e.g., `name:env`) as found in your config.yaml (optional; takes precedence over project name).
- `--select`: Optional comma-separated thread IDs to select. If not provided, you will be prompted to select threads interactively. If you press Enter, all threads will be selected.
- `--output-dir`: Optional directory to save the JSON output files. Defaults to the current directory.

**Configuration File:**

- The script will read the ddn config file at `~/.ddn/config.yaml` containing your PromptQL project secret keys if it exists. See `sample_config.yml` for an example structure.
- The API key for requests is read from the selected project's secret key in this config file.

**Environment Variable:**

- `BASE_URL`: The base URL for the PromptQL API. Set this in your `.env` file or as an environment variable. Example: `BASE_URL=https://promptql.ddn.hasura.app`

**Private Data Plane:**

- Private data planes are supported, but you must specify your `BASE_URL` to reflect your data plane.

## Example

```
python main.py --project-name alive-urchin-6152 --select 3c0bbb82-82b2-475c-8193-d03e7fee0d42 --output-dir ./output
```

This will fetch the selected threads and save each to a file named after the thread's title (or thread_id if no title) plus a timestamp, in the `output` directory.

If you omit `--project-name` and `--project-id`, you will be shown a list of projects and can select one interactively.

**NOTE:** I want to use the PAT stored in ~/.ddn/config.yaml. If anyone knows how to use a PAT to authenticate an API call, let me know.

## Error Handling

The script provides user-friendly messages for common HTTP errors:

- **404 (Not Found):** "Error: Thread not found with the provided ID."
- **403 (Forbidden):** "Error: Unauthorized access. Check your authentication token."
- **500 (Internal Server Error):** "Error: Internal server error. Please try again later."

For other HTTP errors, it displays the status code and any error details returned by the server in a formatted manner.

## Running Tests

To run the unit tests:

```sh
pytest
```

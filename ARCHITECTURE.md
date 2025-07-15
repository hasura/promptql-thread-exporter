# e Architecture

## Overview

Export PromptQL threads from a project

This project uses [python] and leverages LLM tools (e.g., Claude-code, Aider, Cursor, aichat) for development.

## Structure

- `.cursorignore`: Excludes files from Cursor context.
- `.cursor/rules/`: Custom rules for Cursor behavior.
- `.env`: Environment variables (keep secret).
- `.env_example`: Template for environment variables.

## Setup

1. Copy `.env_example` to `.env` and fill in values.
2. Run the project with [uv run script.py] (adjust as needed).

## CLI Script Details

- **main.py**: Contains the CLI logic, argument parsing using argparse, HTTP requests using requests, error handling, and output to console or file. The script now uses a config file at `~/.ddn/config.yaml` to manage project secret keys. The user can specify a project via `--project-name` or `--project-id`, or select one interactively. The API key is read from the selected project in the config file and used in the `Authorization: api-key <API_KEY>` header for all requests.
- **tests/test_main.py**: Unit tests for the fetch_thread function using pytest and mocking.
- State is managed locally within the script. The script connects to the external PromptQL API via HTTP GET requests.
- Dependencies are managed via pyproject.toml and uv.

## New Features (2024-06)

- **Config File and Project Selection:**
  - The CLI now requires a config file at `~/.ddn/config.yaml` containing your PromptQL project secret keys.
  - The user can specify a project via `--project-name` or `--project-id`, or select one interactively from the config file.
  - The API key is read from the selected project and used for all API requests.
- **BASE_URL Environment Variable:**
  - The API base URL is set via the `BASE_URL` environment variable (see `.env_example`).
- **Thread List Fetching and Selection:**
  - The CLI fetches the list of threads from `/playground/threads` using the selected project's API key.
  - Threads can be selected via the `--select` CLI argument (comma-separated thread IDs) or interactively via a prompt.
  - If no selection is made, all threads are selected by default.
- **Per-Thread Output:**
  - Each selected thread is downloaded and saved to a file named `{thread_title or thread_id}_{timestamp}.json` in the specified output directory (or current directory by default).

## API Key Selection Logic

The CLI supports three ways to provide the API key, in the following priority order:

1. **Command-line flag**: `--api-key` (highest priority)
2. **Environment variable**: `API_KEY`
3. **Config file**: `~/.ddn/config.yaml` (lowest priority)

If the API key is not provided via the CLI or environment, the config file is used as a fallback. This logic ensures flexibility for automation, scripting, and interactive use.

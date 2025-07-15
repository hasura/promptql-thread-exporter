import argparse
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

import requests
import sys
import os
import time
from dotenv import load_dotenv
import questionary
import yaml
import signal


logging.basicConfig(level=logging.ERROR)

DEFAULT_OUTPUT_DIR = "promptql_threads"


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML config file from the given path."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_project_key_from_config(config: Dict[str, Any], project_id: Optional[str], project_name: Optional[str]) -> Tuple[str, str]:
    """Get the secret key and project display name from config based on project_id or project_name.
    Removes any colon and suffix from project_name for matching."""
    projects = config.get('promptql_secret_keys', {})
    for k, v in projects.items():
        name, *_ = k.split(':', 1)
        # Remove any colon and suffix from project_name for matching
        cleaned_project_name = project_name.split(
            ':', 1)[0] if project_name else None
        if (project_id and project_id == k) or (cleaned_project_name and cleaned_project_name == name):
            return v, k
    return None, None


def prompt_for_project(config: Dict[str, Any]) -> Tuple[str, str]:
    """Prompt user to select a project from config, return (secret_key, project_key).
    Handles quitting via menu, CTRL-C, or ESC/cancel."""
    projects = config.get('promptql_secret_keys', {})
    quit_choice = questionary.Choice(title="Quit (q)", value="__QUIT__")
    choices = [questionary.Choice(title=k.split(':', 1)[0], value=k)
               for k in projects.keys()] + [quit_choice]
    while True:
        try:
            selected = questionary.select(
                "Select a project:",
                choices=choices,
                instruction="Select 'Quit (q)' to exit, or press CTRL-C to quit."
            ).ask()
            if selected is None:
                print("\nExiting by user request (cancelled/CTRL-C/ESC).\n")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\nExiting by user request (CTRL-C).\n")
            sys.exit(0)
        if not selected:
            print("Warning: You must select a project (or 'Quit (q)' to exit).\n")
            continue
        if selected == "__QUIT__":
            print("Exiting by user request.")
            sys.exit(0)
        return projects[selected], selected


def fetch_thread(thread_id: str, api_key: str, base_url: str) -> Dict[str, Any]:
    """Fetch thread data from the PromptQL API."""
    if not thread_id.strip() or not api_key.strip():
        raise ValueError("Thread ID and API key must be non-empty strings.")
    url = f"{base_url}/playground/threads/{thread_id}"
    headers = {"Authorization": f"api-key {api_key}",
               "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def fetch_thread_list(api_key: str, base_url: str) -> List[Dict[str, Any]]:
    """Fetch a list of threads from the PromptQL API."""
    url = f"{base_url}/playground/threads"
    headers = {"Authorization": f"api-key {api_key}",
               "Content-Type": "application/json"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def select_threads(threads: List[Dict[str, Any]], select_ids: Optional[List[str]] = None, base_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """Select threads by IDs or interactively with checkboxes.
    Handles quitting via menu, CTRL-C, or ESC/cancel."""
    if select_ids:
        selected = [t for t in threads if t.get("thread_id") in select_ids]
        return selected
    if base_url:
        print(f"\nPromptQL API BASE_URL: {base_url}\n")
    all_threads_choice = questionary.Choice(
        title="ALL THREADS", value="__ALL__")
    quit_choice = questionary.Choice(title="Quit (q)", value="__QUIT__")
    choices = [all_threads_choice] + [
        questionary.Choice(title=(t.get("title") or t.get(
            "thread_id")), value=t.get("thread_id"))
        for t in threads
    ] + [quit_choice]
    while True:
        try:
            selected_ids = questionary.checkbox(
                "Select threads to export (space to select, enter to confirm):",
                choices=choices,
                instruction="Select 'Quit (q)' to exit, or press CTRL-C to quit."
            ).ask()
            if selected_ids is None:
                print("\nExiting by user request (cancelled/CTRL-C/ESC).\n")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\nExiting by user request (CTRL-C).\n")
            sys.exit(0)
        if selected_ids and "__QUIT__" in selected_ids:
            print("Exiting by user request.")
            sys.exit(0)
        if not selected_ids:
            print(
                "Warning: You must select at least one thread (or 'Quit (q)' to exit).\n")
            continue
        if "__ALL__" in selected_ids:
            return threads
        return [t for t in threads if t.get("thread_id") in selected_ids]


def handle_sigint(signum, frame):
    print("\nExiting by user request (CTRL-C).\n")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_sigint)


def main() -> None:
    """Main entry point for the CLI script."""
    load_dotenv()
    parser = argparse.ArgumentParser(description="Fetch PromptQL thread data.")
    parser.add_argument("--api-key", required=False, type=str,
                        help="API key for PromptQL (overrides config and env)")
    parser.add_argument("--project-name", required=False,
                        type=str, help="Project name from config.yaml (optional)")
    parser.add_argument("--project-id", required=False, type=str,
                        help="Project id (key) from config.yaml (optional)")
    parser.add_argument("--select", type=str,
                        help="Comma-separated thread IDs to select (optional)")
    parser.add_argument("--output-dir", type=str,
                        help="Directory to save thread files (optional)")
    args = parser.parse_args()

    base_url = os.environ.get("BASE_URL") or "https://promptql.ddn.hasura.app"
    config_path = os.path.expanduser("~/.ddn/config.yaml")
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)
    config = load_config(config_path)

    # API key selection logic: CLI flag > ENV > config.yaml
    api_key = args.api_key or os.environ.get("API_KEY")
    project_key = None
    if not api_key:
        # Project selection logic (only if API key not provided)
        if args.project_id or args.project_name:
            api_key, project_key = get_project_key_from_config(
                config, args.project_id, args.project_name)
            if not api_key:
                print(
                    "Error: Project not found in config for the given --project-id or --project-name.")
                sys.exit(1)
        else:
            api_key, project_key = prompt_for_project(config)
    # If api_key is still None after all attempts, error out
    if not api_key:
        print("Error: No API key provided via --api-key, API_KEY env var, or config.yaml.")
        sys.exit(1)

    try:
        try:
            threads = fetch_thread_list(api_key, base_url)
        except requests.HTTPError as http_err:
            print(
                f"Error: Unable to fetch threads. This may indicate an incorrect API key or BASE_URL.\nDetails: {http_err}")
            sys.exit(1)
        if not threads:
            print(
                "Error: No threads found. This may indicate an incorrect API key or BASE_URL.")
            sys.exit(1)
        select_ids = [tid.strip()
                      for tid in args.select.split(",")] if args.select else None
        selected_threads = select_threads(threads, select_ids, base_url)
        output_dir = args.output_dir or os.path.join(
            os.getcwd(), DEFAULT_OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)
        for thread in selected_threads:
            thread_id = thread.get("thread_id")
            title = thread.get("title") or thread_id
            safe_title = "".join(c if c.isalnum() or c in (
                "-_") else "_" for c in title)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_title}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            data = fetch_thread(thread_id, api_key, base_url)
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)
            print(f"Saved thread '{title}' to {filepath}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()

"""
Main module for JIRA Manager.
"""
from typing import Optional
import argparse
import sys
from datetime import datetime
from .jira_client import JIRAClient
from .config import jira_config

def get_client(host: Optional[str] = None, 
               username: Optional[str] = None, 
               api_token: Optional[str] = None) -> JIRAClient:
    """
    Get a configured JIRA client instance.
    
    Args:
        host (Optional[str]): JIRA host URL. If None, uses config value
        username (Optional[str]): JIRA username. If None, uses config value
        api_token (Optional[str]): JIRA API token. If None, uses config value
        
    Returns:
        JIRAClient: Configured JIRA client instance
        
    Raises:
        ValueError: If required configuration is missing
    """
    # Use provided values or fall back to config
    jira_host = host or jira_config.JIRA_HOST
    jira_username = username or jira_config.JIRA_USERNAME
    jira_api_token = api_token or jira_config.JIRA_API_TOKEN
    
    # Validate configuration
    if not all([jira_host, jira_username, jira_api_token]):
        raise ValueError(
            "Missing JIRA configuration. Either provide values directly or "
            "set them in config/jira_config_local.py"
        )
    
    return JIRAClient(
        server_url=jira_host,
        username=jira_username,
        api_token=jira_api_token
    )

def list_epics(project_key: str, label: str) -> None:
    """
    List all epics in a project with a specific label.
    
    Args:
        project_key (str): The JIRA project key
        label (str): The label to filter epics by
    """
    try:
        client = get_client()
        epics = client.get_epics_by_label(project_key, label)
        
        if not epics:
            print(f"No epics found in project {project_key} with label '{label}'")
            return
            
        print(f"\nEpics in project {project_key} with label '{label}':")
        print("-" * 50)
        for epic in epics:
            print(f"{epic.key}: {epic.summary}")
            
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def list_stories(epic_key: str) -> None:
    """List all stories under an epic with their due dates."""
    try:
        client = get_client()
        stories = client.get_stories_by_epic(epic_key)
        
        if not stories:
            print(f"No stories found under epic {epic_key}")
            return
            
        print(f"\nStories under epic {epic_key}:")
        print("-" * 50)
        for story in stories:
            due_date = story.due_date.strftime("%Y-%m-%d") if story.due_date else "No due date"
            print(f"{story.key}: {story.summary} (Due: {due_date})")
            
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="JIRA Project Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List epics command
    list_epics_parser = subparsers.add_parser("list_epics", help="List epics by project and label")
    list_epics_parser.add_argument("project_key", help="JIRA project key")
    list_epics_parser.add_argument("label", help="Label to filter epics by")
    
    # List stories command
    list_stories_parser = subparsers.add_parser("list_stories", help="List stories under an epic")
    list_stories_parser.add_argument("epic_key", help="Epic key (e.g., PROJ-123)")
    
    args = parser.parse_args()
    
    if args.command == "list_epics":
        list_epics(args.project_key, args.label)
    elif args.command == "list_stories":
        list_stories(args.epic_key)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()

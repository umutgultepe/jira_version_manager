"""
Main module for JIRA Manager.
"""
from typing import Optional, List
import argparse
import sys
from datetime import datetime
from .jira_client import JIRAClient
from .config import jira_config
from .fix_version_manager import FixVersionManager, Action, ActionType
from .models import Epic, Story, FixVersion
from .release_renderer import ReleaseRenderer

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

def list_versions(project_key: str) -> None:
    """List all unreleased versions in a project with their release dates."""
    try:
        client = get_client()
        versions = client.get_unreleased_versions(project_key)
        
        if not versions:
            print(f"No unreleased versions found in project {project_key}")
            return
            
        print(f"\nUnreleased versions in project {project_key}:")
        print("-" * 50)
        for version in versions:
            release_date = version.release_date.strftime("%Y-%m-%d") if version.release_date else "No release date"
            print(f"{version.name}: {version.description or 'No description'} (Release: {release_date})")
            
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def _print_recommendations(version_manager: FixVersionManager, epic: Epic, stories: List[Story], indent: str = "") -> None:
    """
    Print recommendations for an epic and its stories.
    
    Args:
        version_manager: The version manager to get recommendations from
        epic: The epic to process
        stories: List of stories under the epic
        indent: String to use for indentation (default: "")
    """
    print(f"{indent}Epic {epic.key}: {epic.summary}")
    print(f"{indent}" + "-" * 70)
    
    # Get recommendation for epic
    epic_action = version_manager.get_recommended_action(epic)
    print_action(epic_action, indent)
    
    if stories:
        print(f"\n{indent}Stories:")
        print(f"{indent}" + "-" * 70)
        for story in stories:
            story_action = version_manager.get_recommended_action(story)
            print_action(story_action, indent)
    else:
        print(f"\n{indent}No stories found under this epic")

def print_action(action: Action, indent: str = "") -> None:
    """
    Print a recommended action in a formatted way.
    
    Args:
        action: The action to print
        indent: String to use for indentation (default: "")
    """
    issue_type = "Epic" if isinstance(action.issue, Epic) else "Story"
    print(f"{indent}{issue_type} {action.issue.key}: {action.issue.summary}")
    print(f"{indent}  URL: {jira_config.JIRA_HOST}/browse/{action.issue.key}")
    
    if action.action_type == ActionType.NO_ACTION:
        print(f"{indent}  Action: No action needed ({action.reason})")
    elif action.action_type == ActionType.ASSIGN_TO_VERSION:
        print(f"{indent}  Action: Assign to version {action.fix_version.name}, due date is {action.get_due_date()}")
    elif action.action_type == ActionType.INELIGIBLE:
        print(f"{indent}  Action: Cannot assign version ({action.reason})")
    if action.comment:
        print(f"{indent}  Comment: {action.comment}")
    print()

def _apply_action_with_prompt(action: Action, version_manager: FixVersionManager) -> None:
    """
    Prompt user to apply an action and handle the response.
    
    Args:
        action: The action to potentially apply
        version_manager: The version manager to use for applying the action
    """
    if action.action_type != ActionType.NO_ACTION:
        if action.action_type == ActionType.INELIGIBLE:
            print(f"NOTE: This action is ineligible: {action.reason}")
        if input("Apply this action? (y/N): ").lower() == 'y':
            response = version_manager.apply_action(action)
            if response.success:
                print("Successfully applied action")
            else:
                print(f"Failed to apply action: {response.error_message}")

def apply_actions_for_epic(epic_key: str, versions: Optional[List[FixVersion]] = None) -> None:
    """List and optionally apply recommended fix version actions for an epic and its stories."""
    try:
        client = get_client()
        project_key = epic_key.split('-')[0]
        if versions is None:
            versions = client.get_unreleased_versions(project_key)

        if not versions:
            print(f"No unreleased versions found in project {project_key}")
            return
            
        version_manager = FixVersionManager(versions, client)
        
        epic = client.get_epic(epic_key)
        stories = client.get_stories_by_epic(epic_key)
        
        print(f"\nRecommended fix version actions for epic {epic_key} and its stories:")
        print("-" * 70)
        
        # Process epic
        epic_action = version_manager.get_recommended_action(epic)
        print_action(epic_action)
        _apply_action_with_prompt(epic_action, version_manager)
        
        # Process stories
        if stories:
            print("\nStories:")
            print("-" * 70)
            for story in stories:
                story_action = version_manager.get_recommended_action(story)
                print_action(story_action)
                _apply_action_with_prompt(story_action, version_manager)
        else:
            print("\nNo stories found under this epic")
            
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def list_recommended_actions_for_epic(epic_key: str) -> None:
    """List recommended fix version actions for an epic and its stories."""
    try:
        client = get_client()
        project_key = epic_key.split('-')[0]
        
        versions = client.get_unreleased_versions(project_key)
        if not versions:
            print(f"No unreleased versions found in project {project_key}")
            return
            
        version_manager = FixVersionManager(versions)
        epic = client.get_epic(epic_key)
        stories = client.get_stories_by_epic(epic_key)
        
        print(f"\nRecommended fix version actions for epic {epic_key} and its stories:")
        print("-" * 70)
        _print_recommendations(version_manager, epic, stories)
            
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def list_recommended_actions_for_project(project_key: str, label: str) -> None:
    """List recommended fix version actions for all epics with a label and their stories."""
    try:
        client = get_client()
        
        versions = client.get_unreleased_versions(project_key)
        if not versions:
            print(f"No unreleased versions found in project {project_key}")
            return
            
        epics = client.get_epics_by_label(project_key, label)
        if not epics:
            print(f"No epics found in project {project_key} with label '{label}'")
            return
            
        version_manager = FixVersionManager(versions, client)
        print(f"\nRecommended fix version actions for epics labeled '{label}' in {project_key}:")
        
        for epic in epics:
            print("\n" + "=" * 70)
            stories = client.get_stories_by_epic(epic.key)
            _print_recommendations(version_manager, epic, stories)
            
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def apply_actions_for_project(project_key: str, label: str) -> None:
    """Apply recommended fix version actions for all epics with a label and their stories."""
    try:
        client = get_client()
        
        versions = client.get_unreleased_versions(project_key)
        if not versions:
            print(f"No unreleased versions found in project {project_key}")
            return
            
        epics = client.get_epics_by_label(project_key, label)
        if not epics:
            print(f"No epics found in project {project_key} with label '{label}'")
            return
            
        print(f"\nProcessing fix version actions for epics labeled '{label}' in {project_key}:")
        
        for epic in epics:
            print("\n" + "=" * 70)
            print(f"Processing epic {epic.key}")
            print("=" * 70)
            apply_actions_for_epic(epic.key, versions=versions)
            
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def get_project_issues_for_next_fix_version(project_key: str) -> None:
    """
    List all issues assigned to the next upcoming fix version, sorted by assignee.
    
    Args:
        project_key: The JIRA project key
    """
    try:
        client = get_client()
        renderer = ReleaseRenderer(client)
        
        # Get and print the CSV content
        csv_content = renderer.render_release_manifest([project_key])
        print(csv_content)
            
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def render_release_manifest() -> None:
    """
    Generate a release manifest for all configured projects.
    """
    try:
        if not jira_config.PROJECT_KEYS:
            print("No projects configured. Please add PROJECT_KEYS to your configuration.")
            return
            
        client = get_client()
        renderer = ReleaseRenderer(client)
        
        # Get and print the CSV content for all projects
        csv_content = renderer.render_release_manifest(jira_config.PROJECT_KEYS)
        print(csv_content)
            
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def apply_actions(label: str) -> None:
    """
    Apply recommended fix version actions for all labeled epics across all configured projects.
    
    Args:
        label: Label to filter epics by
    """
    try:
        if not jira_config.PROJECT_KEYS:
            print("No projects configured. Please add PROJECT_KEYS to your configuration.")
            return
            
        for project_key in jira_config.PROJECT_KEYS:
            print(f"\nProcessing project {project_key}:")
            print("=" * 70)
            apply_actions_for_project(project_key, label)
            
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
    
    # List versions command
    list_versions_parser = subparsers.add_parser("list_versions", help="List unreleased versions in a project")
    list_versions_parser.add_argument("project_key", help="JIRA project key")
    
    # List recommended actions command
    list_actions_parser = subparsers.add_parser(
        "list_actions_for_epic", 
        help="List recommended fix version actions for an epic and its stories"
    )
    list_actions_parser.add_argument("epic_key", help="Epic key (e.g., PROJ-123)")
    
    # List recommended actions for project command
    list_project_actions_parser = subparsers.add_parser(
        "list_actions_for_project", 
        help="List recommended fix version actions for all labeled epics and their stories"
    )
    list_project_actions_parser.add_argument("project_key", help="JIRA project key")
    list_project_actions_parser.add_argument("label", help="Label to filter epics by")
    
    # Apply actions command
    apply_actions_parser = subparsers.add_parser(
        "apply_actions_for_epic", 
        help="Apply recommended fix version actions for an epic and its stories"
    )
    apply_actions_parser.add_argument("epic_key", help="Epic key (e.g., PROJ-123)")
    
    # Apply actions for project command
    apply_project_actions_parser = subparsers.add_parser(
        "apply_actions_for_project", 
        help="Apply recommended fix version actions for all labeled epics and their stories"
    )
    apply_project_actions_parser.add_argument("project_key", help="JIRA project key")
    apply_project_actions_parser.add_argument("label", help="Label to filter epics by")
    
    # Get next version issues command
    next_version_issues_parser = subparsers.add_parser(
        "get_project_issues_for_next_fix_version",
        help="List all issues for the next upcoming fix version"
    )
    next_version_issues_parser.add_argument("project_key", help="JIRA project key")
    
    # Render release manifest command
    render_manifest_parser = subparsers.add_parser(
        "render_release_manifest",
        help="Generate a release manifest for all configured projects"
    )
    
    # Apply actions across all projects command
    apply_all_actions_parser = subparsers.add_parser(
        "apply_actions",
        help="Apply recommended fix version actions for labeled epics across all configured projects"
    )
    apply_all_actions_parser.add_argument("label", help="Label to filter epics by")
    
    args = parser.parse_args()
    
    if args.command == "list_epics":
        list_epics(args.project_key, args.label)
    elif args.command == "list_stories":
        list_stories(args.epic_key)
    elif args.command == "list_versions":
        list_versions(args.project_key)
    elif args.command == "list_actions_for_epic":
        list_recommended_actions_for_epic(args.epic_key)
    elif args.command == "list_actions_for_project":
        list_recommended_actions_for_project(args.project_key, args.label)
    elif args.command == "apply_actions_for_epic":
        apply_actions_for_epic(args.epic_key)
    elif args.command == "apply_actions_for_project":
        apply_actions_for_project(args.project_key, args.label)
    elif args.command == "get_project_issues_for_next_fix_version":
        get_project_issues_for_next_fix_version(args.project_key)
    elif args.command == "render_release_manifest":
        render_release_manifest()
    elif args.command == "apply_actions":
        apply_actions(args.label)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()

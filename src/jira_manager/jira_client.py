"""
JIRA API client implementation.
"""
from typing import List, Union, Optional
from jira import JIRA
from datetime import datetime

from .models import Epic, Story, User, FixVersion

class JIRAClient:
    def __init__(self, server_url: str, username: str, api_token: str):
        """
        Initialize JIRA client with authentication details.
        
        Args:
            server_url (str): JIRA server URL (e.g., 'https://your-domain.atlassian.net')
            username (str): JIRA username (usually email)
            api_token (str): JIRA API token
        """
        self.server_url = server_url
        self.jira = JIRA(
            server=server_url,
            basic_auth=(username, api_token)
        )

    def get_epics_by_label(self, project_key: str, label: str) -> List[Epic]:
        """
        Retrieve all epics in a project that have a specific label.
        
        Args:
            project_key (str): The project key (e.g., 'PROJ')
            label (str): The label to filter by
            
        Returns:
            List[Epic]: List of Epic objects matching the criteria
            
        Raises:
            JIRAError: If there's an error communicating with JIRA
        """
        # Construct JQL query to find epics with the given label in the project
        jql = f'project = {project_key} AND issuetype = Epic AND labels = {label}'
        
        # Search for issues matching our criteria
        issues = self.jira.search_issues(
            jql,
            fields='summary,description,status,assignee,fixVersions,duedate,issuetype,customfield_10014'
        )
        
        epics = []
        for issue in issues:
            epic = self._create_issue_from_response(issue, project_key)
            epics.append(epic)
        
        return epics 

    def get_stories_by_epic(self, epic_key: str) -> List[Story]:
        """
        Retrieve all stories under a specific epic.
        
        Args:
            epic_key (str): The epic's key (e.g., 'PROJ-123')
            
        Returns:
            List[Story]: List of Story objects under the epic
            
        Raises:
            JIRAError: If there's an error communicating with JIRA
        """
        jql = f'parent = {epic_key} AND issuetype = Story'
        issues = self.jira.search_issues(
            jql,
            fields='summary,description,status,assignee,fixVersions,customfield_10016,priority,created,updated,duedate,issuetype,customfield_10014'  # 10016 is story points
        )
        
        stories = []
        for issue in issues:
            story = self._create_issue_from_response(issue)
            stories.append(story)
        
        return stories 

    def get_unreleased_versions(self, project_key: str) -> List[FixVersion]:
        """
        Retrieve all unreleased fix versions for a project.
        
        Args:
            project_key (str): The project key (e.g., 'PROJ')
            
        Returns:
            List[FixVersion]: List of unreleased FixVersion objects
            
        Raises:
            JIRAError: If there's an error communicating with JIRA
        """
        versions = self.jira.project_versions(project_key)
        
        unreleased_versions = []
        for version in versions:
            # Skip if version is released or archived
            if getattr(version, 'released', False) or getattr(version, 'archived', False):
                continue

            fix_version = FixVersion(
                id=version.id,
                name=version.name,
                description=getattr(version, 'description', None),
                release_date=datetime.strptime(version.releaseDate, '%Y-%m-%d').date()
                if hasattr(version, 'releaseDate') else None
            )
            unreleased_versions.append(fix_version)
        
        return unreleased_versions 

    def get_epic(self, epic_key: str) -> Epic:
        """
        Retrieve a specific epic by its key.
        
        Args:
            epic_key (str): The epic's key (e.g., 'PROJ-123')
            
        Returns:
            Epic: The Epic object
            
        Raises:
            JIRAError: If there's an error communicating with JIRA
        """
        issue = self.jira.issue(
            epic_key,
            fields='summary,description,status,assignee,fixVersions,duedate,issuetype,customfield_10014'
        )
        return self._create_issue_from_response(issue) 

    def _create_user_from_assignee(self, assignee_field) -> Optional[User]:
        """Create a User object from a JIRA assignee field."""
        if not assignee_field:
            return None
        
        return User(
            account_id=assignee_field.accountId,
            email=getattr(assignee_field, 'emailAddress', None),
            display_name=assignee_field.displayName,
            active=assignee_field.active
        )

    def _create_fix_versions_from_field(self, versions_field) -> List[FixVersion]:
        """Create FixVersion objects from a JIRA versions field."""
        fix_versions = []
        if hasattr(versions_field, 'fixVersions'):
            for version in versions_field.fixVersions:
                fix_versions.append(FixVersion(
                    id=version.id,
                    name=version.name,
                    description=getattr(version, 'description', None),
                    release_date=datetime.strptime(version.releaseDate, '%Y-%m-%d').date()
                    if hasattr(version, 'releaseDate') else None
                ))
        return fix_versions

    def _parse_due_date(self, due_date_str: Optional[str]) -> Optional[datetime.date]:
        """Parse a JIRA due date string into a date object."""
        if not due_date_str:
            return None
        return datetime.strptime(due_date_str, '%Y-%m-%d').date()

    def _parse_start_date(self, start_date_str: Optional[str]) -> Optional[datetime.date]:
        """Parse a JIRA start date string into a date object."""
        if not start_date_str:
            return None
        return datetime.strptime(start_date_str, '%Y-%m-%d').date()

    def _create_issue_from_response(self, issue, project_key: str = None) -> Union[Epic, Story]:
        """
        Create an Epic or Story object from a JIRA issue response.
        
        Args:
            issue: JIRA issue object
            project_key (Optional[str]): Project key. If None, extracted from issue key
            
        Returns:
            Union[Epic, Story]: Created issue object
        """
        assignee = self._create_user_from_assignee(issue.fields.assignee)
        fix_versions = self._create_fix_versions_from_field(issue.fields)
        due_date = self._parse_due_date(issue.fields.duedate)
        start_date = self._parse_start_date(getattr(issue.fields, 'customfield_10014', None))
        
        common_args = {
            'project_key': project_key or issue.key.split('-')[0],
            'key': issue.key,
            'summary': issue.fields.summary,
            'description': issue.fields.description,
            'status': issue.fields.status.name,
            'assignee': assignee,
            'fix_versions': fix_versions,
            'due_date': due_date,
            'start_date': start_date
        }
        
        if getattr(issue.fields.issuetype, 'name', None) == 'Epic':
            return Epic(**common_args)
        else:
            return Story(**common_args)

    def assign_fix_version(self, issue: Union[Epic, Story], fix_version: FixVersion) -> None:
        """
        Assign a fix version to an issue, replacing any existing fix versions.
        
        Args:
            issue: The issue to update
            fix_version: The fix version to assign
            
        Raises:
            JIRAError: If there's an error communicating with JIRA
        """
        # Create dict with just the fields we want to update
        update_fields = {
            'fixVersions': [{'id': fix_version.id}]  # JIRA expects a list of version dicts with IDs
        }
        
        # Update the issue
        self.jira.issue(issue.key).update(fields=update_fields) 

    def get_issues_for_fix_version(self, fix_version: FixVersion) -> List[Union[Epic, Story]]:
        """
        Retrieve all epics and stories with a specific fix version.
        
        Args:
            fix_version (FixVersion): The fix version to search for
            
        Returns:
            List[Union[Epic, Story]]: List of Epic and Story objects with the fix version
            
        Raises:
            JIRAError: If there's an error communicating with JIRA
        """
        # Search for issues with the fix version
        jql = f'fixVersion = {fix_version.id} AND issuetype in (Epic, Story)'
        issues = self.jira.search_issues(
            jql,
            fields='summary,description,status,assignee,fixVersions,issuetype,customfield_10016,priority,created,updated,duedate,customfield_10014'
        )
        
        result = []
        for issue in issues:
            result.append(self._create_issue_from_response(issue))
        
        return result 

    def _get_user_timezone(self, user_id: str) -> Optional[str]:
        """Get timezone for a JIRA user."""
        if not user_id:
            return None
        try:
            user = self.jira.user(user_id)
            return getattr(user, 'timeZone', None)
        except:
            return None 

    def comment(self, issue_key: str, comment_text: str) -> None:
        """
        Add a comment to a JIRA issue.
        
        Args:
            issue_key: The issue key (e.g., 'PROJ-123')
            comment_text: The text of the comment to add
            
        Raises:
            JIRAError: If there's an error communicating with JIRA
        """
        self.jira.add_comment(issue_key, comment_text) 

    def add_label(self, issue_key: str, label: str) -> None:
        """
        Add a label to a JIRA issue.
        
        Args:
            issue_key (str): The issue key (e.g., 'PROJ-123')
            label (str): The label to add
            
        Raises:
            JIRAError: If there's an error communicating with JIRA
        """
        issue = self.jira.issue(issue_key)
        current_labels = getattr(issue.fields, 'labels', [])
        
        # Only add the label if it's not already present
        if label not in current_labels:
            current_labels.append(label)
            issue.update(fields={'labels': current_labels}) 
"""
JIRA API client implementation.
"""
from typing import List, Union
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
            fields='summary,description,status,assignee,fixVersions,duedate'
        )
        
        epics = []
        for issue in issues:
            epic = self._create_epic_from_issue(issue, project_key)
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
            fields='summary,description,status,assignee,fixVersions,customfield_10016,priority,created,updated,duedate'  # 10016 is story points
        )
        
        stories = []
        for issue in issues:
            # Convert assignee to User if it exists
            assignee = None
            if hasattr(issue.fields, 'assignee') and issue.fields.assignee:
                assignee = User(
                    account_id=issue.fields.assignee.accountId,
                    email=getattr(issue.fields.assignee, 'emailAddress', None),
                    display_name=issue.fields.assignee.displayName,
                    active=issue.fields.assignee.active
                )
            
            # Convert fix versions
            fix_versions = []
            if hasattr(issue.fields, 'fixVersions'):
                for version in issue.fields.fixVersions:
                    fix_versions.append(FixVersion(
                        id=version.id,
                        name=version.name,
                        description=getattr(version, 'description', None),
                        release_date=datetime.strptime(version.releaseDate, '%Y-%m-%d').date()
                        if hasattr(version, 'releaseDate') else None
                    ))
            if issue.fields.duedate:
                duedate = datetime.strptime(issue.fields.duedate, '%Y-%m-%d').date()
            else:
                duedate = None
            
            story = Story(
                project_key=issue.key.split('-')[0],
                key=issue.key,
                summary=issue.fields.summary,
                description=issue.fields.description,
                status=issue.fields.status.name,
                assignee=assignee,
                fix_versions=fix_versions,
                due_date=duedate,
            )
            
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
            fields='summary,description,status,assignee,fixVersions,duedate'
        )
        return self._create_epic_from_issue(issue) 

    def _create_epic_from_issue(self, issue, project_key: str = None) -> Epic:
        """
        Create an Epic object from a JIRA issue response.
        
        Args:
            issue: JIRA issue object
            project_key (Optional[str]): Project key. If None, extracted from issue key
            
        Returns:
            Epic: Created Epic object
        """
        # Convert assignee to User object if it exists
        assignee = None
        if hasattr(issue.fields, 'assignee') and issue.fields.assignee:
            assignee = User(
                account_id=issue.fields.assignee.accountId,
                email=getattr(issue.fields.assignee, 'emailAddress', None),
                display_name=issue.fields.assignee.displayName,
                active=issue.fields.assignee.active
            )
        
        # Convert fix versions to FixVersion objects
        fix_versions = []
        if hasattr(issue.fields, 'fixVersions'):
            for version in issue.fields.fixVersions:
                fix_versions.append(FixVersion(
                    id=version.id,
                    name=version.name,
                    description=getattr(version, 'description', None),
                    release_date=datetime.strptime(version.releaseDate, '%Y-%m-%d').date() 
                    if hasattr(version, 'releaseDate') else None
                ))
        
        return Epic(
            project_key=project_key or issue.key.split('-')[0],
            key=issue.key,
            summary=issue.fields.summary,
            description=issue.fields.description,
            status=issue.fields.status.name,
            assignee=assignee,
            fix_versions=fix_versions,
            due_date=datetime.strptime(issue.fields.duedate, '%Y-%m-%d').date()
            if issue.fields.duedate else None
        ) 

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
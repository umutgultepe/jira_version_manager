"""
Module for rendering release-related information.
"""
import csv
from io import StringIO
from typing import List, Tuple
from datetime import datetime
from .jira_client import JIRAClient
from .config import jira_config

class ReleaseRenderer:
    """Renders release-related information in various formats."""
    
    def __init__(self, jira_client: JIRAClient):
        """
        Initialize the renderer.
        
        Args:
            jira_client: Configured JIRA client instance
        """
        self.jira_client = jira_client 

    def _init_csv_writer(self) -> Tuple[StringIO, csv.writer]:
        """Initialize a CSV writer with an in-memory buffer."""
        output_buffer = StringIO()
        csv_writer = csv.writer(
            output_buffer,
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )
        return output_buffer, csv_writer

    def render_release_manifest(self, project_keys: List[str]) -> str:
        """
        Render a release manifest for all projects.
        
        Args:
            project_keys: List of project keys to process
            
        Returns:
            str: CSV content as string
        """
        buffer, writer = self._init_csv_writer()
        
        # Write header
        writer.writerow([
            "Project Timezone", "Assignee Name", "Assignee Email", 
            "Issue Key", "Issue Summary", "Issue URL",
            "Fix Version", "Release Date", "Manager Email"
        ])
        
        for project_key in project_keys:
            self._render_release_manifest_for_project(project_key, writer)
            
        return buffer.getvalue()
    
    def _get_project_timezone(self, project_key: str) -> str:
        """Get timezone for a project from configuration."""
        return jira_config.PROJECT_TO_TIMEZONE.get(project_key)
    
    def _get_project_manager(self, project_key: str) -> str:
        """Get manager's email for a project from configuration."""
        return jira_config.PROJECT_TO_MANAGER.get(project_key)

    def _render_release_manifest_for_project(self, project_key: str, writer: csv.writer) -> None:
        """
        Render a release manifest for a specific project.
        
        Args:
            project_key: JIRA project key
            writer: CSV writer to use
        """
        # Get unreleased versions
        versions = self.jira_client.get_unreleased_versions(project_key)
        if not versions:
            return
            
        # Find the next version (closest future date)
        today = datetime.now().date()
        future_versions = [v for v in versions if v.release_date and v.release_date > today]
        if not future_versions:
            return
            
        next_version = min(future_versions, key=lambda v: v.release_date)
        
        # Get and sort issues
        issues = self.jira_client.get_issues_for_fix_version(next_version)
        sorted_issues = sorted(
            issues,
            key=lambda x: (
                x.assignee.display_name.lower() if x.assignee else "zzz",  # Unassigned goes to end
                x.key
            )
        )
        
        # Get project info
        project_timezone = self._get_project_timezone(project_key)
        manager_email = self._get_project_manager(project_key)
        
        # Write issues to CSV
        for issue in sorted_issues:
            assignee_name = issue.assignee.display_name if issue.assignee else "<unassigned>"
            assignee_email = issue.assignee.email if issue.assignee else ""
            
            issue_url = f"{self.jira_client.server_url}/browse/{issue.key}"
            
            writer.writerow([
                project_timezone,
                assignee_name,
                assignee_email,
                issue.key,
                issue.summary,
                issue_url,
                next_version.name,
                next_version.release_date.strftime("%Y-%m-%d") if next_version.release_date else "",
                manager_email
            ])
        
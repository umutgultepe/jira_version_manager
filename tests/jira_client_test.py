"""
Tests for JIRA client functionality.
"""
from datetime import datetime

import pytest

from test_data import mock_epic, mock_jira, client
from jira_manager.models import Epic, User, FixVersion, Story

def test_get_epics_by_label(client, mock_jira, mock_epic_response, mock_epic):
    """Test getting epics by label."""
    mock_jira.search_issues.return_value = [mock_epic_response]
    
    epics = client.get_epics_by_label("PROJ", "feature")
    
    mock_jira.search_issues.assert_called_once_with(
        'project = PROJ AND issuetype = Epic AND labels = feature',
        fields='summary,description,status,assignee,fixVersions,duedate,issuetype,customfield_10014'
    )
    assert len(epics) == 1
    assert epics[0] == mock_epic

def test_get_epics_by_label_no_epics(client, mock_jira):
    """Test getting epics by label when no epics exist."""
    # Setup mock response
    mock_jira.search_issues.return_value = []
    
    # Call the method
    epics = client.get_epics_by_label("PROJ", "feature")
    
    # Verify search was called with correct JQL
    mock_jira.search_issues.assert_called_once_with(
        'project = PROJ AND issuetype = Epic AND labels = feature',
        fields='summary,description,status,assignee,fixVersions,duedate,issuetype'
    )
    
    # Verify empty response
    assert len(epics) == 0
    assert isinstance(epics, list)

def assert_epic_fields(epic: Epic, project_key: str):
    assert epic.project_key == project_key
    assert epic.key == "PROJ-123"
    assert epic.summary == "Test Epic"
    assert epic.description == "Epic description"
    assert epic.status == "In Progress"
    
    # Verify assignee
    assert isinstance(epic.assignee, User)
    assert epic.assignee.account_id == "user123"
    assert epic.assignee.email == "john.doe@example.com"
    assert epic.assignee.display_name == "John Doe"
    assert epic.assignee.active is True
    
    # Verify fix version
    assert len(epic.fix_versions) == 1
    fix_version = epic.fix_versions[0]
    assert isinstance(fix_version, FixVersion)
    assert fix_version.id == "10000"
    assert fix_version.name == "v1.0"
    assert fix_version.description == "First Release"
    assert fix_version.release_date == datetime.strptime("2024-12-31", "%Y-%m-%d").date()

def test_get_stories_by_epic(client, mock_jira, mock_story_response, mock_story):
    """Test getting stories under an epic."""
    mock_jira.search_issues.return_value = [mock_story_response]
    
    stories = client.get_stories_by_epic("PROJ-123")
    
    mock_jira.search_issues.assert_called_once_with(
        'parent = PROJ-123 AND issuetype = Story',
        fields='summary,description,status,assignee,fixVersions,customfield_10016,priority,created,updated,duedate,issuetype,customfield_10014'
    )
    assert len(stories) == 1
    assert stories[0] == mock_story

def test_get_unreleased_versions(client, mock_jira, mock_version_response, mock_project_version):
    """Test getting unreleased versions from a project."""
    # Setup mock response
    mock_jira.project_versions.return_value = mock_version_response
    
    # Call the method
    versions = client.get_unreleased_versions("PROJ")
    
    # Verify project_versions was called with correct project key
    mock_jira.project_versions.assert_called_once_with("PROJ")
    
    # Verify the response
    assert len(versions) == 1
    version = versions[0]
    
    # Verify individual fields except name
    assert version.id == mock_project_version.id
    assert version.description == mock_project_version.description
    assert version.release_date == mock_project_version.release_date

def test_assign_fix_version(client, mock_jira, mock_story, mock_project_version):
    """Test assigning a fix version to an issue."""
    # Call the method
    client.assign_fix_version(mock_story, mock_project_version)
    
    # Verify JIRA API was called correctly
    mock_issue = mock_jira.issue.return_value
    mock_jira.issue.assert_called_once_with(mock_story.key)
    mock_issue.update.assert_called_once_with(
        fields={'fixVersions': [{'id': mock_project_version.id}]}
    )

def test_get_epic(client, mock_jira, mock_epic_response, mock_epic):
    """Test getting a specific epic."""
    mock_jira.issue.return_value = mock_epic_response
    
    epic = client.get_epic("PROJ-123")
    
    mock_jira.issue.assert_called_once_with(
        "PROJ-123",
        fields='summary,description,status,assignee,fixVersions,duedate,issuetype,customfield_10014'
    )
    assert epic == mock_epic

def test_get_issues_for_fix_version(client, mock_jira, mock_epic_response, mock_story_response, mock_project_version):
    """Test getting issues with a specific fix version."""
    mock_jira.search_issues.return_value = [mock_epic_response, mock_story_response]
    
    issues = client.get_issues_for_fix_version(mock_project_version)
    
    mock_jira.search_issues.assert_called_once_with(
        f'fixVersion = {mock_project_version.id} AND issuetype in (Epic, Story)',
        fields='summary,description,status,assignee,fixVersions,issuetype,customfield_10016,priority,created,updated,duedate'
    )
    assert len(issues) == 2
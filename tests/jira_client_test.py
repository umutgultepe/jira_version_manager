"""
Tests for JIRA client functionality.
"""
from datetime import datetime
from unittest.mock import Mock

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
    assert epics[0].key == mock_epic.key
    assert epics[0].summary == mock_epic.summary
    assert epics[0].description == mock_epic.description
    assert epics[0].status == mock_epic.status
    assert epics[0].due_date == mock_epic.due_date
    assert epics[0].start_date == mock_epic.start_date

def test_get_epics_by_label_no_epics(client, mock_jira):
    """Test getting epics by label when no epics exist."""
    mock_jira.search_issues.return_value = []
    
    epics = client.get_epics_by_label("PROJ", "feature")
    
    mock_jira.search_issues.assert_called_once_with(
        'project = PROJ AND issuetype = Epic AND labels = feature',
        fields='summary,description,status,assignee,fixVersions,duedate,issuetype,customfield_10014'
    )
    
    assert len(epics) == 0
    assert isinstance(epics, list)

def assert_epic_fields(epic: Epic, project_key: str):
    assert epic.project_key == project_key
    assert epic.key == "PROJ-123"
    assert epic.summary == "Test Epic"
    assert epic.description == "Epic description"
    assert epic.status == "In Progress"
    assert epic.start_date == datetime.strptime("2024-01-15", "%Y-%m-%d").date()
    
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
    assert stories[0].key == mock_story.key
    assert stories[0].summary == mock_story.summary
    assert stories[0].description == mock_story.description
    assert stories[0].status == mock_story.status
    assert stories[0].due_date == mock_story.due_date
    assert stories[0].start_date == mock_story.start_date

def test_get_unreleased_versions(client, mock_jira, mock_version_response, mock_project_version):
    """Test getting unreleased versions from a project."""
    mock_jira.project_versions.return_value = mock_version_response
    
    versions = client.get_unreleased_versions("PROJ")
    
    mock_jira.project_versions.assert_called_once_with("PROJ")
    
    assert len(versions) == 1
    version = versions[0]
    
    assert version.id == mock_project_version.id
    assert version.name == mock_project_version.name
    assert version.description == mock_project_version.description
    assert version.release_date == mock_project_version.release_date

def test_assign_fix_version(client, mock_jira, mock_story, mock_project_version):
    """Test assigning a fix version to an issue."""
    mock_issue = Mock()
    mock_jira.issue.return_value = mock_issue
    
    client.assign_fix_version(mock_story, mock_project_version)
    
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
    assert epic.key == mock_epic.key
    assert epic.summary == mock_epic.summary
    assert epic.description == mock_epic.description
    assert epic.status == mock_epic.status
    assert epic.due_date == mock_epic.due_date
    assert epic.start_date == mock_epic.start_date

def test_get_issues_for_fix_version(client, mock_jira, mock_epic_response, mock_story_response, mock_project_version):
    """Test getting issues with a specific fix version."""
    mock_jira.search_issues.return_value = [mock_epic_response, mock_story_response]
    
    issues = client.get_issues_for_fix_version(mock_project_version)
    
    mock_jira.search_issues.assert_called_once_with(
        f'fixVersion = {mock_project_version.id} AND issuetype in (Epic, Story)',
        fields='summary,description,status,assignee,fixVersions,issuetype,customfield_10016,priority,created,updated,duedate,customfield_10014'
    )
    assert len(issues) == 2
    assert isinstance(issues[0], Epic)
    assert isinstance(issues[1], Story)
    assert issues[0].key == mock_epic_response.key
    assert issues[1].key == mock_story_response.key
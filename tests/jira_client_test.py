"""
Tests for JIRA client functionality.
"""
from datetime import datetime

import pytest

from test_data import mock_epic, mock_jira, client
from jira_manager.models import Epic, User, FixVersion

def test_get_epics_by_label_single_epic(client, mock_jira, mock_epic_response, mock_epic):
    """Test getting epics by label when one epic exists."""
    # Setup mock response
    mock_jira.search_issues.return_value = [mock_epic_response]
    
    # Call the method
    epics = client.get_epics_by_label("PROJ", "feature")
    
    # Verify search was called with correct JQL
    mock_jira.search_issues.assert_called_once_with(
        'project = PROJ AND issuetype = Epic AND labels = feature',
        fields='summary,description,status,assignee,fixVersions,duedate'
    )
    
    # Verify the response
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
        fields='summary,description,status,assignee,fixVersions,duedate'
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
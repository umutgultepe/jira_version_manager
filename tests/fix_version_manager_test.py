"""
Tests for fix version manager functionality.
"""
import pytest
from jira_manager.fix_version_manager import FixVersionManager, ActionType
from jira_manager.models import Epic, Story

def test_fix_version_manager_init(mock_project_version, mock_jira):
    """Test FixVersionManager initialization."""
    versions = [mock_project_version]
    manager = FixVersionManager(versions, mock_jira)
    assert manager.fix_versions == versions 

def test_get_recommended_action_has_version(epic_with_fix_version, mock_project_version, mock_jira):
    """Test getting recommended action when issue already has a fix version."""
    manager = FixVersionManager([mock_project_version], mock_jira)
    action = manager.get_recommended_action(epic_with_fix_version)
    
    assert action.action_type == ActionType.NO_ACTION
    assert action.fix_version is None
    assert action.reason == "Issue already has a fix version"
    assert action.issue == epic_with_fix_version

def test_get_recommended_action_no_due_date(epic_no_due_date, mock_project_version, mock_jira):
    """Test getting recommended action when issue has no due date."""
    manager = FixVersionManager([mock_project_version], mock_jira)
    action = manager.get_recommended_action(epic_no_due_date)
    
    assert action.action_type == ActionType.NO_ACTION
    assert action.fix_version is None
    assert action.reason == "No due date"
    assert action.issue == epic_no_due_date

def test_get_recommended_action_late_due_date(epic_late_due_date, mock_project_version, mock_jira):
    """Test getting recommended action when issue due date is later than all versions."""
    manager = FixVersionManager([mock_project_version], mock_jira)
    action = manager.get_recommended_action(epic_late_due_date)
    
    assert action.action_type == ActionType.NO_ACTION
    assert action.fix_version is None
    assert action.reason == "Due date later than all fix versions"
    assert action.issue == epic_late_due_date

def test_get_recommended_action_needs_version(epic_needs_version, mock_project_version, mock_jira):
    """Test getting recommended action when issue needs a fix version."""
    manager = FixVersionManager([mock_project_version], mock_jira)
    action = manager.get_recommended_action(epic_needs_version)
    
    assert action.action_type == ActionType.ASSIGN_TO_VERSION
    assert action.fix_version == mock_project_version
    assert action.reason is None
    assert action.issue == epic_needs_version 

@pytest.mark.parametrize("issue,expected", [
    (
        Story(
            project_key="PROJ",
            key="PROJ-123",
            summary="Normal story",
            description="A regular story",
            status="To Do",
            assignee=None,
            fix_versions=[],
            due_date=None,
            start_date=None
        ),
        (True, None)
    ),
    (
        Story(
            project_key="PROJ",
            key="PROJ-123",
            summary="Investigation spike",
            description="A spike",
            status="To Do",
            assignee=None,
            fix_versions=[],
            due_date=None,
            start_date=None
        ),
        (False, "Summary contains ineligible keyword: Investigation spike")
    ),
    (
        Story(
            project_key="PROJ",
            key="PROJ-123",
            summary="Normal story",
            description="A regular story",
            status="Won't Fix",
            assignee=None,
            fix_versions=[],
            due_date=None,
            start_date=None
        ),
        (False, "Status is Won't Fix")
    ),
    (
        Epic(
            project_key="PROJ",
            key="PROJ-123",
            summary="Epic with spike in name",
            description="An epic",
            status="To Do",
            assignee=None,
            fix_versions=[],
            due_date=None,
            start_date=None
        ),
        (True, "Issue is an Epic")
    )
])
def test_is_issue_eligible(issue, expected, mock_jira):
    """Test issue eligibility checks."""
    manager = FixVersionManager([], mock_jira)  # Empty list is fine for this test
    assert manager.is_issue_eligible(issue) == expected 
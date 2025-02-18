"""
Test data and fixtures for JIRA Manager tests.
"""
from datetime import datetime, date
from unittest.mock import Mock

import pytest
from jira import JIRA

from jira_manager.jira_client import JIRAClient
from jira_manager.models import Epic, User, FixVersion, Story


class Name(object):
    def __init__(self, name):
        self.name = name

@pytest.fixture
def mock_jira(monkeypatch):
    """Mock JIRA client instance."""
    mock = Mock(spec=JIRA)
    monkeypatch.setattr('jira_manager.jira_client.JIRA', lambda *args, **kwargs: mock)
    return mock

@pytest.fixture
def client(mock_jira):
    """Create a JIRAClient instance with mock credentials."""
    return JIRAClient(
        server_url="https://test.atlassian.net",
        username="test@example.com",
        api_token="dummy-token"
    )

@pytest.fixture
def mock_assignee():
    """Create a mock JIRA user."""
    return Mock(
        accountId="user123",
        emailAddress="john.doe@example.com",
        displayName="John Doe",
        active=True
    )

@pytest.fixture
def mock_fix_version():
    """Create a mock JIRA version."""
    version = Mock()
    version.id = "10000"
    version.name = "v1.0"
    version.description = "First Release"
    version.releaseDate = "2024-12-31"
    return version

@pytest.fixture
def mock_epic_response(mock_assignee, mock_fix_version):
    """Create a mock JIRA API response for an epic."""
    status = Mock()
    status.name = "In Progress"
    issue_type = Mock()
    issue_type.name = "Epic"
    return Mock(
        key="PROJ-123",
        fields=Mock(
            summary="Test Epic",
            description="Epic description",
            status=status,
            assignee=mock_assignee,
            fixVersions=[mock_fix_version],
            duedate="2024-12-31",
            issuetype=issue_type,
            customfield_10014="2024-01-15"  # Start date
        )
    )

@pytest.fixture
def mock_epic(mock_assignee, mock_fix_version) -> Epic:
    """Create a mock Epic instance."""
    return Epic(
        project_key="PROJ",
        key="PROJ-123",
        summary="Test Epic",
        description="Epic description",
        status="In Progress",
        assignee=mock_assignee,
        fix_versions=[mock_fix_version],
        due_date=date(2024, 12, 31),
        start_date=date(2024, 1, 15)
    )

@pytest.fixture
def mock_story_fields(mock_assignee, mock_fix_version):
    """Create mock fields for a JIRA story."""
    return Mock(
        summary="Test Story",
        description="Story description",
        status=Name(name="To Do"),
        assignee=mock_assignee,
        fixVersions=[mock_fix_version],
        customfield_10016=5.0,  # Story points
        priority=Name(name="High"),
        duedate="2024-01-02"  # Changed from dueDate to duedate with YYYY-MM-DD format
    )

@pytest.fixture
def mock_story_response(mock_assignee, mock_fix_version):
    """Create a mock JIRA API response for a story."""
    status = Mock()
    status.name = "In Progress"
    issue_type = Mock()
    issue_type.name = "Story"
    return Mock(
        key="PROJ-456",
        fields=Mock(
            summary="Test Story",
            description="Story description",
            status=status,
            assignee=mock_assignee,
            fixVersions=[mock_fix_version],
            duedate="2024-12-31",
            issuetype=issue_type,
            customfield_10014="2024-02-01",  # Start date
            customfield_10016=5.0  # Story points
        )
    )

@pytest.fixture
def mock_story(mock_assignee, mock_fix_version) -> Story:
    """Create a mock Story instance."""
    return Story(
        project_key="PROJ",
        key="PROJ-456",
        summary="Test Story",
        description="Story description",
        status="In Progress",
        assignee=mock_assignee,
        fix_versions=[mock_fix_version],
        due_date=date(2024, 12, 31),
        start_date=date(2024, 2, 1)
    )

@pytest.fixture
def mock_project_version() -> FixVersion:
    """Create an unreleased JIRA version."""
    return FixVersion(
        id="10001",
        name="v2.0",
        description="Second Release",
        release_date=datetime.strptime("2024-06-30", "%Y-%m-%d").date()
    )

@pytest.fixture
def mock_released_version() -> FixVersion:
    """Create a released JIRA version."""
    return FixVersion(
        id="10000",
        name="v1.0",
        description="First Release",
        release_date=datetime.strptime("2024-01-31", "%Y-%m-%d").date()
    )

@pytest.fixture
def mock_archived_version() -> FixVersion:
    """Create an archived JIRA version."""
    return FixVersion(
        id="9999",
        name="v0.9",
        description="Beta Release",
        release_date=datetime.strptime("2023-12-31", "%Y-%m-%d").date()
    )

@pytest.fixture
def mock_version_response():
    """Create mock JIRA API responses for versions."""
    def create_version(id, name, description, release_date, released, archived):
        version = Mock()
        version.id = id
        version.name = name
        version.description = description
        version.releaseDate = release_date
        version.released = released
        version.archived = archived
        return version

    return [
        create_version(
            "10001",
            "v2.0",
            "Second Release",
            "2024-06-30",
            False,
            False
        ),
        create_version(
            "10000",
            "v1.0",
            "First Release",
            "2024-01-31",
            True,
            False
        ),
        create_version(
            "9999",
            "v0.9",
            "Beta Release",
            "2023-12-31",
            False,
            True
        )
    ]

@pytest.fixture
def epic_with_fix_version(mock_project_version) -> Epic:
    """Create an epic that already has a fix version."""
    return Epic(
        project_key="PROJ",
        key="PROJ-123",
        summary="Test Epic",
        description="Epic description",
        status="In Progress",
        assignee=None,
        fix_versions=[mock_project_version],
        due_date=date(2024, 6, 1)
    )

@pytest.fixture
def epic_no_due_date() -> Epic:
    """Create an epic with no due date."""
    return Epic(
        project_key="PROJ",
        key="PROJ-123",
        summary="Test Epic",
        description="Epic description",
        status="In Progress",
        assignee=None,
        fix_versions=[],
        due_date=None
    )

@pytest.fixture
def epic_late_due_date() -> Epic:
    """Create an epic with a due date later than all fix versions."""
    return Epic(
        project_key="PROJ",
        key="PROJ-123",
        summary="Test Epic",
        description="Epic description",
        status="In Progress",
        assignee=None,
        fix_versions=[],
        due_date=date(2025, 1, 1)
    )

@pytest.fixture
def epic_needs_version() -> Epic:
    """Create an epic that needs a fix version."""
    return Epic(
        project_key="PROJ",
        key="PROJ-123",
        summary="Test Epic",
        description="Epic description",
        status="In Progress",
        assignee=None,
        fix_versions=[],
        due_date=date(2024, 5, 1)
    ) 
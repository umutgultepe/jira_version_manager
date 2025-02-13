"""
Test data and fixtures for JIRA Manager tests.
"""
from datetime import datetime, date
from unittest.mock import Mock

import pytest
from jira import JIRA

from jira_manager.jira_client import JIRAClient
from jira_manager.models import Epic, User, FixVersion, Story

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
    return Mock(
        id="10000",
        name="v1.0",
        description="First Release",
        releaseDate="2024-12-31"
    )

@pytest.fixture
def mock_epic_response(mock_assignee, mock_fix_version):
    """Create a mock JIRA API response for an epic."""
    return Mock(
        key="PROJ-123",
        fields=Mock(
            summary="Test Epic",
            description="Epic description",
            status=Mock(name="In Progress"),
            assignee=mock_assignee,
            fixVersions=[mock_fix_version],
            duedate="2024-12-31"
        )
    )

@pytest.fixture
def mock_epic(mock_epic_response):
    """Create an Epic object matching the mock response."""
    return Epic(
        project_key="PROJ",
        key=mock_epic_response.key,
        summary=mock_epic_response.fields.summary,
        description=mock_epic_response.fields.description,
        status=mock_epic_response.fields.status.name,
        assignee=User(
            account_id=mock_epic_response.fields.assignee.accountId,
            email=mock_epic_response.fields.assignee.emailAddress,
            display_name=mock_epic_response.fields.assignee.displayName,
            active=mock_epic_response.fields.assignee.active
        ),
        fix_versions=[
            FixVersion(
                id=v.id,
                name=v.name,
                description=v.description,
                release_date=datetime.strptime(v.releaseDate, "%Y-%m-%d").date()
            )
            for v in mock_epic_response.fields.fixVersions
        ],
        due_date=datetime.strptime(mock_epic_response.fields.duedate, "%Y-%m-%d").date()
    )

@pytest.fixture
def mock_story_fields(mock_assignee, mock_fix_version):
    """Create mock fields for a JIRA story."""
    return Mock(
        summary="Test Story",
        description="Story description",
        status=Mock(name="To Do"),
        assignee=mock_assignee,
        fixVersions=[mock_fix_version],
        customfield_10016=5.0,  # Story points
        priority=Mock(name="High"),
        duedate="2024-01-02"  # Changed from dueDate to duedate with YYYY-MM-DD format
    )

@pytest.fixture
def mock_story_response(mock_story_fields):
    """Create a mock JIRA API response for a story."""
    return Mock(
        key="PROJ-456",
        fields=mock_story_fields
    )

@pytest.fixture
def mock_story(mock_story_response):
    """Create a Story object matching the mock response."""
    return Story(
        project_key="PROJ",
        key=mock_story_response.key,
        summary=mock_story_response.fields.summary,
        description=mock_story_response.fields.description,
        status=mock_story_response.fields.status.name,
        assignee=User(
            account_id=mock_story_response.fields.assignee.accountId,
            email=mock_story_response.fields.assignee.emailAddress,
            display_name=mock_story_response.fields.assignee.displayName,
            active=mock_story_response.fields.assignee.active
        ),
        fix_versions=[
            FixVersion(
                id=v.id,
                name=v.name,
                description=v.description,
                release_date=datetime.strptime(v.releaseDate, "%Y-%m-%d").date()
            )
            for v in mock_story_response.fields.fixVersions
        ],
        due_date=datetime.strptime(mock_story_response.fields.duedate, '%Y-%m-%d')
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
    return [
        Mock(
            **{
                'id': "10001",
                'name': "v2.0",
                'description': "Second Release",
                'releaseDate': "2024-06-30",
                'released': False,
                'archived': False
            }
        ),
        Mock(
            **{
                'id': "10000",
                'name': "v1.0",
                'description': "First Release",
                'releaseDate': "2024-01-31",
                'released': True,
                'archived': False
            }
        ),
        Mock(
            **{
                'id': "9999",
                'name': "v0.9",
                'description': "Beta Release",
                'releaseDate': "2023-12-31",
                'released': False,
                'archived': True
            }
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
        status="In Progress"
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
        due_date=date(2024, 5, 1)
    ) 
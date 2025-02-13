"""
Test data and fixtures for JIRA Manager tests.
"""
from datetime import datetime
from unittest.mock import Mock

import pytest
from jira import JIRA

from jira_manager.jira_client import JIRAClient
from jira_manager.models import Epic, User, FixVersion

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
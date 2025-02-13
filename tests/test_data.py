"""
Test data and fixtures for JIRA Manager tests.
"""
from datetime import datetime
from unittest.mock import Mock

import pytest
from jira import JIRA

from jira_manager.jira_client import JIRAClient

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
def mock_epic_fields(mock_assignee, mock_fix_version):
    """Create mock fields for a JIRA epic."""
    return Mock(
        summary="Test Epic",
        description="Epic description",
        status=Mock(name="In Progress"),
        assignee=mock_assignee,
        fixVersions=[mock_fix_version],
        duedate="2024-12-31"
    )

@pytest.fixture
def mock_epic(mock_epic_fields):
    """Create a complete mock JIRA epic."""
    return Mock(
        key="PROJ-123",
        fields=mock_epic_fields
    ) 
"""
PyTest configuration file.
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)

# Import fixtures from test_data
from test_data import (  # noqa
    mock_jira,
    client,
    mock_assignee,
    mock_fix_version,
    mock_epic_response,
    mock_epic,
    mock_story_fields,
    mock_story_response,
    mock_story,
    mock_project_version,
    mock_released_version,
    mock_archived_version,
    mock_version_response,
    epic_with_fix_version,
    epic_no_due_date,
    epic_late_due_date,
    epic_needs_version
) 
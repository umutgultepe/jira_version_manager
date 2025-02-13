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
    mock_epic_fields,
    mock_epic
) 
"""
Data models for JIRA entities.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class User:
    """Represents a JIRA User."""
    account_id: str
    email: str
    display_name: str
    active: bool = True
    time_zone: Optional[str] = None

@dataclass
class FixVersion:
    """Represents a JIRA Fix Version/Release."""
    id: str
    name: str
    description: Optional[str] = None
    release_date: Optional[datetime] = None

@dataclass
class Issue:
    """Base class for JIRA issues."""
    project_key: str
    key: str
    summary: str
    description: Optional[str]
    status: str
    assignee: Optional[User]
    fix_versions: List[FixVersion]
    due_date: Optional[datetime.date] = None
    start_date: Optional[datetime.date] = None

@dataclass
class Epic(Issue):
    """Represents a JIRA epic."""
    pass

@dataclass
class Story(Issue):
    """Represents a JIRA story."""
    pass 
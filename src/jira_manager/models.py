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
class Epic:
    """Represents a JIRA Epic."""
    project_key: str
    key: str
    summary: str
    description: Optional[str] = None
    status: str = "To Do"
    assignee: Optional[User] = None
    fix_versions: List[FixVersion] = None
    due_date: Optional[datetime] = None
    
    def __post_init__(self):
        if self.fix_versions is None:
            self.fix_versions = []

@dataclass
class Story:
    """Represents a JIRA Story/Issue."""
    project_key: str
    key: str
    summary: str
    epic: Optional[Epic] = None
    description: Optional[str] = None
    status: str = "To Do"
    assignee: Optional[User] = None
    fix_versions: List[FixVersion] = None
    due_date: Optional[datetime] = None
    reporter: Optional[User] = None
    
    def __post_init__(self):
        if self.fix_versions is None:
            self.fix_versions = [] 
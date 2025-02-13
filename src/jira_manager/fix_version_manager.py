"""
Manager class for handling JIRA fix versions.
"""
import datetime
from typing import List, Optional, Union
from .models import FixVersion
from .models import Epic, Story
from enum import Enum
from dataclasses import dataclass

class ActionType(Enum):
    NO_ACTION = 0
    ASSIGN_TO_VERSION = 1
    COMMENT = 2

@dataclass
class Action:
    action_type: ActionType
    fix_version: Optional[FixVersion]
    comment: Optional[str]
    issue: Union[Epic, Story]
    reason: str

    def get_due_date(self) -> datetime.date:
        return self.issue.due_date

class FixVersionManager:
    """Manages operations on JIRA fix versions."""
    
    def __init__(self, fix_versions: List[FixVersion]):
        """
        Initialize with a list of fix versions.
        
        Args:
            fix_versions (List[FixVersion]): List of fix versions to manage
        """
        self.fix_versions = fix_versions 

    def get_next_fix_version(self, issue: Union[Epic, Story]) -> Optional[FixVersion]:
        """
        Get the next fix version after the issue's due date.
        
        Args:
            issue (Union[Epic, Story]): The issue to find next version for
            
        Returns:
            Optional[FixVersion]: The next fix version after issue's due date, or None if not found
        """
        if not issue.due_date:
            return None

        # Filter versions with release dates after issue due date
        valid_versions = [v for v in self.fix_versions 
                         if v.release_date and v.release_date > issue.due_date]
        
        if not valid_versions:
            return None
            
        # Return version with earliest release date
        return min(valid_versions, key=lambda v: v.release_date)

    def get_recommended_action(self, issue: Union[Epic, Story]) -> Action:
        if issue.fix_versions:
            return Action(
                action_type=ActionType.NO_ACTION,
                issue=issue,
                fix_version=None,
                comment=None,
                reason="Issue already has a fix version",
            )

        if not issue.due_date:
            return Action(
                action_type=ActionType.NO_ACTION, 
                issue=issue,
                fix_version=None, 
                comment=None, 
                reason="No due date",
            )

        next_fix_version = self.get_next_fix_version(issue)
        if not next_fix_version:
            return Action(
                action_type=ActionType.NO_ACTION, 
                issue=issue,
                fix_version=None, 
                comment=None, 
                reason="Due date later than all fix versions",
            )

        return Action(
            action_type=ActionType.ASSIGN_TO_VERSION,
            issue=issue,
            fix_version=next_fix_version,
            comment=None,
            reason=None,
        )
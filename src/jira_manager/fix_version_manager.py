"""
Manager class for handling JIRA fix versions.
"""
import datetime
from typing import List, Optional, Union
from .models import FixVersion
from .models import Epic, Story
from enum import Enum
from dataclasses import dataclass
from .jira_client import JIRAClient

class ActionType(Enum):
    NO_ACTION = 0
    ASSIGN_TO_VERSION = 1
    COMMENT = 2
    INELIGIBLE = 3

@dataclass
class Action:
    action_type: ActionType
    fix_version: Optional[FixVersion]
    comment: Optional[str]
    issue: Union[Epic, Story]
    reason: str

    def get_due_date(self) -> datetime.date:
        return self.issue.due_date

@dataclass
class ActionResponse:
    action: Action
    success: bool
    error_message: Optional[str] = None

class FixVersionManager:
    """Manages operations on JIRA fix versions."""
    
    def __init__(self, fix_versions: List[FixVersion], jira_client: JIRAClient):
        """
        Initialize with a list of fix versions.
        
        Args:
            fix_versions (List[FixVersion]): List of fix versions to manage
        """
        self.fix_versions = fix_versions 
        self.jira_client = jira_client

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

        is_eligible, ineligibility_reason = self.is_issue_eligible(issue)
        if not is_eligible:
            return Action(
                action_type=ActionType.INELIGIBLE,
                issue=issue,
                fix_version=next_fix_version,
                comment=None,
                reason=ineligibility_reason,
            )

        return Action(
            action_type=ActionType.ASSIGN_TO_VERSION,
            issue=issue,
            fix_version=next_fix_version,
            comment=None,
            reason=None,
        )

    def apply_action(self, action: Action) -> ActionResponse:
        """
        Apply an action to a JIRA issue.
        
        Args:
            action: The action to apply
        """
        try:
            if action.action_type == ActionType.ASSIGN_TO_VERSION:
                self.jira_client.assign_fix_version(action.issue, action.fix_version)
                return ActionResponse(action=action, success=True, error_message=None)
        except Exception as e:
            return ActionResponse(action=action, success=False, error_message=str(e))
        

    def is_issue_eligible(self, issue: Union[Epic, Story]) -> tuple[bool, Optional[str]]:
        """
        Check if an issue is eligible for fix version assignment.
        
        Args:
            issue: The issue to check
            
        Returns:
            tuple[bool, Optional[str]]: (is_eligible, reason_if_not_eligible)
        """
        # Epics are not eligible
        if isinstance(issue, Epic):
            return True, "Issue is an Epic"
        
        # Check status
        ineligible_statuses = {"Won't Fix", "Duplicate", "Wontfix"}
        if issue.status.lower() in {s.lower() for s in ineligible_statuses}:
            return False, f"Status is {issue.status}"
        
        # Check for ineligible keywords in name
        ineligible_keywords = {"spike", "investigation", "research", "design", "1-pager", "one pager"}
        if any(keyword in issue.summary.lower() for keyword in ineligible_keywords):
            return False, f"Summary contains ineligible keyword: {issue.summary}"
        
        return True, None
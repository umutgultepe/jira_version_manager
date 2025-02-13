"""
JIRA configuration settings.
Default values can be overridden by creating a jira_config_local.py file.
"""

JIRA_HOST = "https://your-domain.atlassian.net"
JIRA_USERNAME = "your-email@example.com"
JIRA_API_TOKEN = "your-api-token"

# Try to import local config to override default values
try:
    from .jira_config_local import *  # noqa
except ImportError:
    pass 
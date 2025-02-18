# JIRA Manager

A Python-based command-line tool for managing JIRA projects, epics, and stories with a focus on fix version management.

## Features

- Retrieve and manage epics by label
- List stories under epics
- Manage fix versions across projects
- Assign fix versions to issues
- Generate release manifests
- Add comments to issues
- Handle unreleased versions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jira_manager.git
cd jira_manager
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the template configuration file:
```bash
cp src/jira_manager/config/jira_config_local.template.py src/jira_manager/config/jira_config_local.py
```

2. Edit `jira_config_local.py` with your JIRA credentials:
```python
JIRA_HOST = "https://your-domain.atlassian.net"
JIRA_USERNAME = "your-email@example.com"
JIRA_API_TOKEN = "your-api-token"
PROJECT_KEYS = ["PROJ1", "PROJ2"]  # Add your project keys
```

To get your JIRA API token:
1. Log in to https://id.atlassian.com/manage/api-tokens
2. Click "Create API token"
3. Copy the generated token

## Usage

### List Epics by Label
```bash
python -m jira_manager list_epics PROJ feature
```

### List Stories Under an Epic
```bash
python -m jira_manager list_stories PROJ-123
```

### List Unreleased Versions
```bash
python -m jira_manager list_versions PROJ
```

### List Recommended Fix Version Actions
```bash
python -m jira_manager list_actions_for_epic PROJ-123
```

### Apply Fix Version Actions
```bash
python -m jira_manager apply_actions_for_epic PROJ-123
```

### Generate Release Manifest
```bash
python -m jira_manager render_release_manifest
```

### Add Comment to Issue
```bash
python -m jira_manager comment PROJ-123 "Your comment text"
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Project Structure
```
jira_manager/
├── src/
│   └── jira_manager/
│       ├── config/
│       │   ├── jira_config.py
│       │   ├── jira_config_local.py
│       │   └── jira_config_local.template.py
│       ├── models.py
│       ├── jira_client.py
│       ├── fix_version_manager.py
│       ├── release_renderer.py
│       └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_data.py
│   ├── jira_client_test.py
│   └── fix_version_manager_test.py
├── requirements.txt
└── setup.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 


TODO:
- Fix version correction - right now, it just assumes the assigned fix version is correct. 

from setuptools import setup, find_packages

setup(
    name="jira-manager",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "jira>=3.5.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.1",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to manage JIRA projects",
    keywords="jira, project management",
    python_requires=">=3.7",
) 
"""Pytest configuration and shared fixtures."""

import pytest
from datetime import datetime


@pytest.fixture
def sample_pr_data():
    """Sample pull request data for testing."""
    return [
        {
            "number": 1,
            "state": "closed",
            "created_at": "2024-01-01T00:00:00Z",
            "merged_at": "2024-01-02T00:00:00Z",
            "additions": 100,
            "deletions": 50,
            "changed_files": 5,
        },
        {
            "number": 2,
            "state": "closed",
            "created_at": "2024-01-01T00:00:00Z",
            "merged_at": "2024-01-03T00:00:00Z",
            "additions": 200,
            "deletions": 100,
            "changed_files": 8,
        },
        {
            "number": 3,
            "state": "open",
            "created_at": "2024-01-01T00:00:00Z",
            "merged_at": None,
            "additions": 150,
            "deletions": 75,
            "changed_files": 6,
        },
    ]


@pytest.fixture
def sample_repository_data():
    """Sample repository data for testing."""
    return {
        "id": 12345,
        "name": "test-repo",
        "full_name": "test-owner/test-repo",
        "description": "A test repository",
        "private": False,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "pushed_at": "2024-01-02T00:00:00Z",
        "size": 1024,
        "stargazers_count": 10,
        "watchers_count": 5,
        "language": "Python",
        "forks_count": 2,
        "open_issues_count": 3,
    }

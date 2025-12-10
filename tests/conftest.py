"""
Pytest configuration and fixtures for API tests
"""

import pytest
import sys
from pathlib import Path

# Add the src directory to the path so we can import the app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    """Provide a TestClient for testing the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state():
    """
    Reset the activities state before each test
    to ensure test isolation
    """
    from app import activities
    
    # Save original state
    original_state = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    activities.clear()
    for name, details in original_state.items():
        activities[name] = details

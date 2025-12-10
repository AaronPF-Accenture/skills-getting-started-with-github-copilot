"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Provide a TestClient for testing the API"""
    from app import app
    return TestClient(app)


class TestActivitiesEndpoint:
    """Test the /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_returns_activity_details(self, client):
        """Test that activities have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        # Check a specific activity
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club

    def test_get_activities_returns_participants_list(self, client):
        """Test that participants are returned as a list"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Test the signup endpoint"""

    def test_signup_new_participant(self, client):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_participant_appears_in_list(self, client):
        """Test that a signed-up participant appears in the activities list"""
        email = "test_participant@mergington.edu"
        
        # Sign up
        response = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify in list
        response = client.get("/activities")
        data = response.json()
        assert email in data["Programming Class"]["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_registration(self, client):
        """Test that signing up twice for the same activity fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response2.status_code == 400
        
        data = response2.json()
        assert "already signed up" in data["detail"]


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""

    def test_unregister_existing_participant(self, client):
        """Test unregistering a participant"""
        email = "unregister_test@mergington.edu"
        
        # Sign up first
        client.post(f"/activities/Tennis Club/signup?email={email}")
        
        # Unregister
        response = client.post(
            f"/activities/Tennis Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Tennis Club" in data["message"]

    def test_unregister_removes_participant_from_list(self, client):
        """Test that unregistering removes the participant from the list"""
        email = "remove_test@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Art Studio/signup?email={email}")
        
        # Verify in list
        response = client.get("/activities")
        assert email in response.json()["Art Studio"]["participants"]
        
        # Unregister
        client.post(f"/activities/Art Studio/unregister?email={email}")
        
        # Verify removed from list
        response = client.get("/activities")
        assert email not in response.json()["Art Studio"]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered_participant(self, client):
        """Test unregistering a participant who is not signed up"""
        response = client.post(
            "/activities/Drama Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "not signed up" in data["detail"]


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Redirect status
        assert response.headers["location"] == "/static/index.html"


class TestActivityAvailability:
    """Test activity availability constraints"""

    def test_max_participants_constraint(self, client):
        """Test that activities have max participant limits"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            max_participants = activity_data["max_participants"]
            current_participants = len(activity_data["participants"])
            
            # Verify max_participants is greater than current participants
            assert max_participants >= current_participants


class TestSignupAndUnregisterFlow:
    """Test complete signup and unregister flows"""

    def test_full_signup_unregister_cycle(self, client):
        """Test the complete cycle of signup and unregister"""
        email = "cycle_test@mergington.edu"
        activity = "Debate Team"
        
        # Initial state - not registered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify registered
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify unregistered
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_multiple_signup_unregister_operations(self, client):
        """Test multiple signup and unregister operations"""
        emails = [
            "multi1@mergington.edu",
            "multi2@mergington.edu",
            "multi3@mergington.edu",
        ]
        activity = "Science Club"
        
        # Sign up multiple users
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all are registered
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        for email in emails:
            assert email in participants
        
        # Unregister some users
        for email in emails[:2]:
            response = client.post(f"/activities/{activity}/unregister?email={email}")
            assert response.status_code == 200
        
        # Verify correct users are removed
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        assert emails[0] not in participants
        assert emails[1] not in participants
        assert emails[2] in participants

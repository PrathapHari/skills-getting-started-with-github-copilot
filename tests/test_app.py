"""
Tests for the Mergington High School Activities API
"""

import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient
from app import app

# Create test client
client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities(self):
        """Test fetching all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Check that Tennis Club exists
        assert "Tennis Club" in activities
        assert "description" in activities["Tennis Club"]
        assert "schedule" in activities["Tennis Club"]
        assert "max_participants" in activities["Tennis Club"]
        assert "participants" in activities["Tennis Club"]

    def test_activities_have_required_fields(self):
        """Test that all activities have required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_details in activities.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_details, dict)
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignupEndpoint:
    """Tests for the signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Tennis%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]
        assert "Tennis Club" in result["message"]

    def test_signup_duplicate(self):
        """Test that duplicate signup is rejected"""
        # First signup should succeed
        response1 = client.post(
            "/activities/Tennis%20Club/signup?email=test@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            "/activities/Tennis%20Club/signup?email=test@mergington.edu"
        )
        assert response2.status_code == 400
        result = response2.json()
        assert "already signed up" in result["detail"]

    def test_signup_nonexistent_activity(self):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_signup_updates_participant_list(self):
        """Test that signup adds participant to the list"""
        email = "participant@mergington.edu"
        
        # Get initial participants
        response_before = client.get("/activities")
        activity_before = response_before.json()["Art Studio"]
        initial_count = len(activity_before["participants"])
        
        # Sign up
        response_signup = client.post(
            f"/activities/Art%20Studio/signup?email={email}"
        )
        assert response_signup.status_code == 200
        
        # Get updated participants
        response_after = client.get("/activities")
        activity_after = response_after.json()["Art Studio"]
        updated_count = len(activity_after["participants"])
        
        # Verify participant was added
        assert updated_count == initial_count + 1
        assert email in activity_after["participants"]


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unreg@mergington.edu"
        
        # First sign up
        client.post(f"/activities/Drama%20Club/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Drama%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]

    def test_unregister_not_registered(self):
        """Test unregistering someone who isn't registered"""
        response = client.post(
            "/activities/Science%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "not registered" in result["detail"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from activity that doesn't exist"""
        response = client.post(
            "/activities/Fake%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_unregister_removes_participant(self):
        """Test that unregister removes participant from the list"""
        email = "remove@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Basketball%20Team/signup?email={email}")
        
        # Get participants before unregister
        response_before = client.get("/activities")
        activity_before = response_before.json()["Basketball Team"]
        assert email in activity_before["participants"]
        count_before = len(activity_before["participants"])
        
        # Unregister
        client.post(f"/activities/Basketball%20Team/unregister?email={email}")
        
        # Get participants after unregister
        response_after = client.get("/activities")
        activity_after = response_after.json()["Basketball Team"]
        count_after = len(activity_after["participants"])
        
        # Verify participant was removed
        assert count_after == count_before - 1
        assert email not in activity_after["participants"]

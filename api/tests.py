import pytest
from rest_framework import status
from django.urls import reverse
from .models import Cat, Mission, Target


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.mark.django_db
class TestSCA:

    # 1. Test Cat Creation with Breed Validation
    def test_create_cat_valid_breed(self, api_client):
        url = reverse('cat-list')
        data = {"name": "Agent Meow", "years_of_experience": 3, "breed": "Siberian", "salary": "4500.00"}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_cat_invalid_breed(self, api_client):
        url = reverse('cat-list')
        data = {"name": "Fake Cat", "years_of_experience": 1, "breed": "Golden Retriever", "salary": "100.00"}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 2. Test Mission Target Limits (1 to 3)
    def test_create_mission_target_limit(self, api_client):
        url = reverse('mission-list')
        # Too many targets (4)
        data = {
            "targets": [
                {"name": "T1", "country": "USA"}, {"name": "T2", "country": "USA"},
                {"name": "T3", "country": "USA"}, {"name": "T4", "country": "USA"}
            ]
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 3. Test Note Freezing Logic
    def test_frozen_notes_on_completed_target(self, api_client):
        # Setup: Create mission and target
        mission = Mission.objects.create()
        target = Target.objects.create(mission=mission, name="Target Alpha", country="Ukraine", is_completed=True)

        url = reverse('target-detail', kwargs={'pk': target.pk})
        data = {"notes": "Trying to change notes on completed target"}
        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Notes are frozen" in str(response.data)

    # 4. Test Deletion Restriction
    def test_delete_assigned_mission_fails(self, api_client):
        cat = Cat.objects.create(name="Spy", years_of_experience=2, breed="Siberian", salary=1000)
        mission = Mission.objects.create(cat=cat)

        url = reverse('mission-detail', kwargs={'pk': mission.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

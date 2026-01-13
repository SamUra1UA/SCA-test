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

    # --- 1. SPY CATS ENDPOINTS ---

    def test_create_cat_valid_breed(self, api_client):
        """Test recruiting a cat with a valid breed (TheCatAPI validation)."""
        url = reverse('cat-list')
        data = {
            "name": "Agent Meow",
            "years_of_experience": 3,
            "breed": "Siberian",
            "salary": "4500.00"
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_cat_invalid_breed(self, api_client):
        """Test recruiting a cat with an invalid breed should fail."""
        url = reverse('cat-list')
        data = {
            "name": "Fake Cat",
            "years_of_experience": 1,
            "breed": "Golden Retriever",
            "salary": "100.00"
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_cat_salary_only(self, api_client):
        """Requirement: Only salary should be updatable via PATCH."""
        cat = Cat.objects.create(name="Spy", years_of_experience=2, breed="Siberian", salary=1000)
        url = reverse('cat-detail', kwargs={'pk': cat.pk})

        # Valid update
        response = api_client.patch(url, {"salary": "2000.00"})
        assert response.status_code == status.HTTP_200_OK

        # Invalid update (trying to change name)
        response = api_client.patch(url, {"name": "New Name"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_remove_cat(self, api_client):
        """Test removing a cat from the system."""
        cat = Cat.objects.create(name="Spy", years_of_experience=2, breed="Siberian", salary=1000)
        url = reverse('cat-detail', kwargs={'pk': cat.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    # --- 2. MISSIONS & ASSIGNMENT ---

    def test_create_mission_target_limit(self, api_client):
        """Requirement: Mission must have 1-3 targets."""
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

    def test_assign_cat_to_mission(self, api_client):
        """Test assigning a cat to an available mission."""
        cat = Cat.objects.create(name="Spy", years_of_experience=2, breed="Siberian", salary=1000)
        mission = Mission.objects.create()
        url = reverse('mission-assign-cat', kwargs={'pk': mission.pk})

        response = api_client.patch(url, {"cat_id": cat.id})
        assert response.status_code == status.HTTP_200_OK
        mission.refresh_from_db()
        assert mission.cat == cat

    def test_cat_one_mission_at_a_time(self, api_client):
        """Requirement: One cat can only have one mission."""
        cat = Cat.objects.create(name="Spy", years_of_experience=2, breed="Siberian", salary=1000)
        Mission.objects.create(cat=cat)  # Cat already has a mission

        new_mission = Mission.objects.create()
        url = reverse('mission-assign-cat', kwargs={'pk': new_mission.pk})
        response = api_client.patch(url, {"cat_id": cat.id})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_assigned_mission_fails(self, api_client):
        """Requirement: Cannot delete a mission if a cat is assigned."""
        cat = Cat.objects.create(name="Spy", years_of_experience=2, breed="Siberian", salary=1000)
        mission = Mission.objects.create(cat=cat)

        url = reverse('mission-detail', kwargs={'pk': mission.pk})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # --- 3. TARGETS & INTEL ---

    def test_update_target_notes(self, api_client):
        """Test updating notes on an active target."""
        mission = Mission.objects.create()
        target = Target.objects.create(mission=mission, name="Target Alpha", country="Ukraine")
        url = reverse('target-detail', kwargs={'pk': target.pk})

        response = api_client.patch(url, {"notes": "Top secret intel"})
        assert response.status_code == status.HTTP_200_OK
        target.refresh_from_db()
        assert target.notes == "Top secret intel"

    def test_frozen_notes_on_completed_target(self, api_client):
        """Requirement: Notes frozen if target or mission is completed."""
        mission = Mission.objects.create()
        target = Target.objects.create(
            mission=mission,
            name="Target Alpha",
            country="Ukraine",
            is_completed=True
        )

        url = reverse('target-detail', kwargs={'pk': target.pk})
        data = {"notes": "Trying to change notes on completed target"}
        response = api_client.patch(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Notes are frozen" in str(response.data)

    def test_mission_auto_completes(self, api_client):
        """Requirement: Mission marks as complete when all targets are done."""
        mission = Mission.objects.create()
        target = Target.objects.create(mission=mission, name="T1", country="UK")

        url = reverse('target-detail', kwargs={'pk': target.pk})
        api_client.patch(url, {"is_completed": True})

        mission.refresh_from_db()
        assert mission.is_completed is True
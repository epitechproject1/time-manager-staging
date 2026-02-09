from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from departments.models import Department
from teams.models import Teams

User = get_user_model()


class TeamsViewSetTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="user1@example.com",
            password="password123",
            first_name="User",
            last_name="One",
        )

        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="password123",
            first_name="User",
            last_name="Two",
        )

        self.department = Department.objects.create(name="IT Department")

        self.team1 = Teams.objects.create(
            name="Backend Team",
            description="Team backend",
            owner=self.user,
            department=self.department,
        )
        self.team2 = Teams.objects.create(
            name="Frontend Team",
            description="Team frontend",
            owner=self.user2,
            department=self.department,
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_teams(self):
        url = reverse("teams-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_department(self):
        url = reverse("teams-list")
        response = self.client.get(url, {"department": self.department.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_owner(self):
        url = reverse("teams-list")
        response = self.client.get(url, {"owner": self.user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Backend Team")

    def test_my_teams_action(self):
        url = reverse("teams-my-teams")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["owner"], self.user.id)

    def test_create_team(self):
        url = reverse("teams-list")
        payload = {
            "name": "New Team",
            "description": "Created by test",
        }
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"], self.user.id)
        self.assertEqual(response.data["name"], "New Team")

    def test_retrieve_team(self):
        url = reverse("teams-detail", args=[self.team1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Backend Team")

    def test_update_team(self):
        url = reverse("teams-detail", args=[self.team1.id])
        payload = {
            "name": "Updated Team",
            "description": "Updated description",
            "owner": self.user.id,
            "department": self.department.id,
        }
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Team")
        self.assertEqual(response.data["description"], "Updated description")

    def test_partial_update_team(self):
        url = reverse("teams-detail", args=[self.team1.id])
        payload = {"description": "Partially updated"}
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["description"], "Partially updated")

    def test_delete_team(self):
        url = reverse("teams-detail", args=[self.team1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Teams.objects.filter(id=self.team1.id).exists())

from django.test import TestCase
from django.contrib.auth import get_user_model
from teams.models import Teams
from departments.models import Department

User = get_user_model()


class TeamsModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123"
        )

        self.department = Department.objects.create(
            name="IT Department"
        )

        self.team = Teams.objects.create(
            name="Backend Team",
            description="Team responsible for backend services",
            owner=self.user,
            department=self.department
        )

    def test_team_creation(self):
        """Test que l'équipe est correctement créée"""
        self.assertEqual(self.team.name, "Backend Team")
        self.assertEqual(self.team.description, "Team responsible for backend services")
        self.assertEqual(self.team.owner, self.user)
        self.assertEqual(self.team.department, self.department)

    def test_team_str_method(self):
        """Test de la méthode __str__"""
        expected_str = "Backend Team: Team responsible for backend services"
        self.assertEqual(str(self.team), expected_str)

    def test_team_timestamps(self):
        """Test que les dates sont automatiquement renseignées"""
        self.assertIsNotNone(self.team.created_at)
        self.assertIsNotNone(self.team.updated_at)

    def test_owner_can_be_null(self):
        """Test que owner peut être null"""
        team = Teams.objects.create(
            name="No Owner Team",
            description="Team without owner"
        )
        self.assertIsNone(team.owner)

    def test_department_can_be_null(self):
        """Test que department peut être null"""
        team = Teams.objects.create(
            name="No Department Team",
            description="Team without department"
        )
        self.assertIsNone(team.department)

from django.test import TestCase
from django.contrib.auth import get_user_model
from departments.models import Department
from teams.models import Teams
from teams.serializers import TeamsSerializer

User = get_user_model()


class TeamsSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            first_name="Test",
            last_name="User"
        )

        self.department = Department.objects.create(name="IT Department")

        self.team = Teams.objects.create(
            name="Backend Team",
            description="Team responsible for backend services",
            owner=self.user,
            department=self.department
        )

    def test_serializer_fields(self):
        """Test que le serializer contient tous les champs et valeurs correctes"""
        serializer = TeamsSerializer(self.team)
        data = serializer.data

        self.assertEqual(data["id"], self.team.id)
        self.assertEqual(data["name"], self.team.name)
        self.assertEqual(data["description"], self.team.description)
        self.assertEqual(data["owner"], self.user.id)
        self.assertEqual(data["department"], self.department.id)

        self.assertEqual(data["owner_name"], "Test User")
        self.assertEqual(data["owner_email"], "testuser@example.com")
        self.assertEqual(data["department_name"], "IT Department")

        self.assertIsNotNone(data["created_at"])
        self.assertIsNotNone(data["updated_at"])

    def test_serializer_without_owner_and_department(self):
        """Test le serializer quand owner et department sont null"""
        team = Teams.objects.create(
            name="No Owner Team",
            description="Team without owner and department"
        )
        serializer = TeamsSerializer(team)
        data = serializer.data

        self.assertIsNone(data["owner"])
        self.assertIsNone(data["owner_name"])
        self.assertIsNone(data["owner_email"])
        self.assertIsNone(data["department"])
        self.assertIsNone(data["department_name"])

"""
Tests for the steps API.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Step
from posting.serializers import StepSerializer


STEPS_URL = reverse('posting:step-list')


def detail_url(step_id):
    """Create and return a step detail URL."""
    return reverse('posting:step-detail', args=[step_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicStepsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth us required for retrieving steps."""
        res = self.client.get(STEPS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    

class PrivateStepsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieving_steps(self):
        """Test retrieving a list of steps."""
        Step.objects.create(user=self.user, name='Step 1')
        Step.objects.create(user=self.user, name='Step 2')

        res = self.client.get(STEPS_URL)

        steps = Step.objects.all().order_by('-name')
        serializer = StepSerializer(steps, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_steps_limited_to_user(self):
        """Test list of steps is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Step.objects.create(user=user2, name='Step 1')
        step = Step.objects.create(user=self.user, name='Step 2')

        res = self.client.get(STEPS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], step.name)
        self.assertEqual(res.data[0]['id'], step.id)

    def test_update_step(self):
        """Test updating a step."""
        step = Step.objects.create(user=self.user, name='Step')

        payload = {'name': 'Step update'}
        url = detail_url(step.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        step.refresh_from_db()
        self.assertEqual(step.name, payload['name'])

    def test_delete_step(self):
        """Test deleting a step."""
        step = Step.objects.create(user=self.user, name='Step')

        url = detail_url(step.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        steps = Step.objects.filter(user=self.user)
        self.assertFalse(steps.exists())

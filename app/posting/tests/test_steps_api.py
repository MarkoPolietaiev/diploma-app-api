"""
Tests for the steps API.
"""
import tempfile
import os
from PIL import Image
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Step, Posting
from posting.serializers import StepSerializer


STEPS_URL = reverse('posting:step-list')


def detail_url(step_id):
    """Create and return a step detail URL."""
    return reverse('posting:step-detail', args=[step_id])


def posting_detail_url(posting_id):
    """Create and return a posting detail URL."""
    return reverse('posting:posting-detail', args=[posting_id])


def image_upload_url(step_id):
    """Create and return an image URL."""
    return reverse('posting:step-upload-image', args=[step_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a user."""
    return get_user_model().objects.create_user(email=email, password=password)


def create_posting(user, **params):
    """Create and return a sample posting."""
    defaults = {
        'title': 'Sample posting title',
        'time_minutes': 25,
        'description': 'Sample posting description.',
        'link': 'http://example.com/posting.pdf',
    }
    defaults.update(params)

    posting = Posting.objects.create(user=user, **defaults)
    return posting


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


class ImageUploadTests(TestCase):
    """Tests for image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123',
        )
        self.client.force_authenticate(self.user)
        
        self.posting = create_posting(user=self.user)
        payload = {'steps':[{'name': 'Test Step 1'}]}
        url = posting_detail_url(self.posting.id)
        res = self.client.patch(url, payload, format='json')
        self.posting.refresh_from_db()
        self.step = self.posting.steps.all()[0]

    def tearDown(self):
        self.step.image.delete()
    
    def test_upload_image(self):
        """Test uploading an image to a step."""
        url = image_upload_url(self.posting.steps.all()[0].id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10,10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.posting.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.posting.steps.all()[0].image.path))
    
    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""
        url = image_upload_url(self.posting.steps.all()[0].id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
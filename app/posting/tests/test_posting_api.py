"""
Tests for posting API.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import (
    Posting,
    Tag,
)
from posting.serializers import (
    PostingSerializer,
    PostingDetailSerializer,
)


POSTINGS_URL = reverse('posting:posting-list')


def detail_url(posting_id):
    """Create and return a posting detail URL."""
    return reverse('posting:posting-detail', args=[posting_id])


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


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicPostingAPITests(TestCase):
    """Test unauthorized API requests."""

    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(POSTINGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePostingAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='testpass123')
        self.client.force_authenticate(self.user)
    
    def test_retrieve_postings(self):
        """Test retrieving a lsit of postings."""
        create_posting(user=self.user)
        create_posting(user=self.user)

        res = self.client.get(POSTINGS_URL)

        postings = Posting.objects.all().order_by('-id')
        serializer = PostingSerializer(postings, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_posting_list_limited_to_user(self):
        """Test list of postings is limited to authenticated user."""
        other_user = create_user(
            email='other@example.com',
            password='testpass123',
        )
        create_posting(user=other_user)
        create_posting(user=self.user)

        res = self.client.get(POSTINGS_URL)

        postings = Posting.objects.filter(user=self.user)
        serializer = PostingSerializer(postings, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
    
    def test_get_posting_detail(self):
        """Test get posting detail."""
        posting = create_posting(user=self.user)

        url = detail_url(posting.id)
        res = self.client.get(url)

        serializer = PostingDetailSerializer(posting)
        self.assertEqual(res.data, serializer.data)

    def test_create_posting(self):
        """Test creating a posting."""
        payload = {
            'title': 'Sample posting',
            'time_minutes': 20,
        }
        res = self.client.post(POSTINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        posting = Posting.objects.get(id=res.data['id'])
        for k,v in payload.items():
            self.assertEqual(getattr(posting, k), v)
        self.assertEqual(posting.user, self.user)
    
    def test_partial_update(self):
        """Test partial update of a posting."""
        original_link = 'http://example.com/posting.pdf'
        posting = create_posting(
            user = self.user,
            title='Sample posting title',
            link=original_link,
        )

        payload = {'title': 'New posting title'}
        url = detail_url(posting.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        posting.refresh_from_db()
        self.assertEqual(posting.title, payload['title'])
        self.assertEqual(posting.link, original_link)
        self.assertEqual(posting.user, self.user)

    def test_full_update(self):
        """Test full update of posting."""
        posting = create_posting(
            user=self.user,
            title='Sample posting title',
            link='http://example.com/posting.pdf',
            description='Sample posting description.',
        )

        payload = {
            'title': 'New posting title',
            'link': 'http://example.com/new-posting.pdf',
            'description': 'New posting description.',
            'time_minutes': 15,
        }
        url = detail_url(posting.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        posting.refresh_from_db()
        for k,v in payload.items():
            self.assertEqual(getattr(posting, k), v)
        self.assertEqual(posting.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the posting user results in an error."""
        new_user = create_user(email='user2@example.com', password="testpass123")
        posting = create_posting(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(posting.id)
        self.client.patch(url, payload)

        posting.refresh_from_db()
        self.assertEqual(posting.user, self.user)

    def test_delete_postin(self):
        """Test deleting a posting successful."""
        posting = create_posting(user=self.user)

        url = detail_url(posting.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Posting.objects.filter(id=posting.id).exists())

    def test_delete_other_users_posting_error(self):
        """Test trying to delete another users posting gives error."""
        new_user = create_user(email='user2@example.com', password='testpass123')
        posting = create_posting(user=new_user)

        url = detail_url(posting.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Posting.objects.filter(id=posting.id).exists())
    
    def test_create_posting_with_new_tags(self):
        """Test creating a posting with new tags."""
        payload = {
            'title': 'Test title',
            'time_minutes': 45,
            'tags': [{'name': 'Test tag'}, {'name': 'Test tag2'}]
        }
        res = self.client.post(POSTINGS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        postings = Posting.objects.filter(user=self.user)
        self.assertEqual(postings.count(), 1)
        posting = postings[0]
        self.assertEqual(posting.tags.count(), 2)
        for tag in payload['tags']:
            exists = posting.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)
    
    def test_create_posting_with_existing_tags(self):
        """Test creating a posting with existing tags."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Test title',
            'time_minutes': 45,
            'tags': [{'name': 'Indian'}, {'name': 'Indian 2'}],
        }
        res = self.client.post(POSTINGS_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        postings = Posting.objects.filter(user=self.user)
        self.assertEqual(postings.count(), 1)
        posting = postings[0]
        self.assertEqual(posting.tags.count(), 2)
        self.assertIn(tag_indian, posting.tags.all())
        for tag in payload['tags']:
            exists = posting.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)
    
    def test_create_tag_on_update(self):
        """Test creating tag when updating a posting."""
        posting = create_posting(user=self.user)

        payload = {'tags':[{'name': 'Test Tag 3'}]}
        url = detail_url(posting.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name = 'Test Tag 3')
        self.assertIn(new_tag, posting.tags.all())

    def test_update_posting_assign_tag(self):
        """Test assigning an existing tag when updating a posting."""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        posting = create_posting(user=self.user)
        posting.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(posting.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, posting.tags.all())
        self.assertNotIn(tag_breakfast, posting.tags.all())
    
    def test_clear_tags(self):
        """Test clearing a posting tags."""
        tag = Tag.objects.create(user=self.user, name = 'Test Tag 3')
        posting = create_posting(user=self.user)
        posting.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(posting.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(posting.tags.count(), 0)

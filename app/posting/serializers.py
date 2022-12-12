"""
Serializers for posting APIs
"""
from rest_framework import serializers
from core.models import Posting


class PostingSerializer(serializers.ModelSerializer):
    """Serializer for postings."""

    class Meta:
        model = Posting
        fields = ['id', 'title', 'time_minutes', 'link']
        read_only_fields = ['id']


class PostingDetailSerializer(PostingSerializer):
    """Serializer for posting detail view."""

    class Meta(PostingSerializer.Meta):
        fields = PostingSerializer.Meta.fields + ['description']

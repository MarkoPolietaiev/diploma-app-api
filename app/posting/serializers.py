"""
Serializers for posting APIs
"""
from rest_framework import serializers
from core.models import (
    Posting,
    Tag,
    Step,
)


class StepSerializer(serializers.ModelSerializer):
    """Serializer for steps."""

    class Meta:
        model = Step
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class PostingSerializer(serializers.ModelSerializer):
    """Serializer for postings."""
    tags = TagSerializer(many=True, required=False)
    steps = StepSerializer(many=True, required=False)

    class Meta:
        model = Posting
        fields = ['id', 'title', 'time_minutes', 'link', 'tags', 'steps',]
        read_only_fields = ['id']
    
    def _get_or_create_tags(self, tags, posting):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            posting.tags.add(tag_obj)
    
    def _get_or_create_steps(self, steps, posting):
        """Handle getting or creating steps as needed."""
        auth_user = self.context['request'].user
        for step in steps:
            step_obj, created = Step.objects.get_or_create(
                user=auth_user,
                **step,
            )
            posting.steps.add(step_obj)

    def create(self, validated_data):
        """Create a posting."""
        tags = validated_data.pop('tags', [])
        steps = validated_data.pop('steps', [])
        posting = Posting.objects.create(**validated_data)
        self._get_or_create_tags(tags, posting)
        self._get_or_create_steps(steps, posting)
        return posting
    
    def update(self, instance, validated_data):
        """Update posting."""
        tags = validated_data.pop('tags', [])
        steps = validated_data.pop('steps', [])
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)
        if steps is not None:
            instance.steps.clear()
            self._get_or_create_steps(steps, instance)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class PostingDetailSerializer(PostingSerializer):
    """Serializer for posting detail view."""

    class Meta(PostingSerializer.Meta):
        fields = PostingSerializer.Meta.fields + ['description']


class StepImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading step image."""

    class Meta:
        model = Step
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image':{'required': True}}

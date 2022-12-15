"""
Views for the posting APIs.
"""
from rest_framework import (
    viewsets,
    mixins,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import (
    Posting,
    Tag,
    Step,
)
from posting import serializers


class PostingViewSet(viewsets.ModelViewSet):
    """View for manage posting APIs."""
    serializer_class = serializers.PostingDetailSerializer
    queryset = Posting.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve postings for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.PostingSerializer
        
        return self.serializer_class
    
    def perform_create(self, serializer):
        """Create a new posting."""
        serializer.save(user=self.request.user)        


class BasePostingAttrViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Base viewset for posting attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve tags for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(BasePostingAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class StepViewSet(BasePostingAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.StepSerializer
    queryset = Step.objects.all()

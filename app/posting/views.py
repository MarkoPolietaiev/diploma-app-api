"""
Views for the posting APIs.
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import (
    viewsets,
    mixins,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import (
    Posting,
    Tag,
    Step,
)
from posting import serializers

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Coma separated list of IDs to filter',
            ),
            OpenApiParameter(
                'steps',
                OpenApiTypes.STR,
                description='Coma separated list of step IDs to filter',
            )
        ]
    )
)
class PostingViewSet(viewsets.ModelViewSet):
    """View for manage posting APIs."""
    serializer_class = serializers.PostingDetailSerializer
    queryset = Posting.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        "1,2,3"
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve postings for authenticated user."""
        tags = self.request.query_params.get('tags')
        steps = self.request.query_params.get('steps')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if steps:
            step_ids = self._params_to_ints(steps)
            queryset = queryset.filter(steps__id__in=step_ids)
        
        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()
            

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.PostingSerializer
        
        return self.serializer_class
    
    def perform_create(self, serializer):
        """Create a new posting."""
        serializer.save(user=self.request.user)  


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0,1],
                description='Filter by items assigned to postings.',
            ),
        ]
    )
)
class BasePostingAttrViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Base viewset for posting attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve tags for authenticated user."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(posting__isnull=False)

        return queryset.filter(
            user=self.request.user
            ).order_by('-name').distinct()


class TagViewSet(BasePostingAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class StepViewSet(BasePostingAttrViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.StepSerializer
    queryset = Step.objects.all()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'upload_image':
            return serializers.StepImageSerializer
        
        return self.serializer_class

    @action(methods=['POST'], detail=True, url_path='upload_image')      
    def upload_image(self, request, pk=None):
        """Upload an image to a step."""
        posting = self.get_object()
        serializer = self.get_serializer(posting, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

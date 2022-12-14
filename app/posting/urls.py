"""
URL mappings for the posting app.
"""
from django.urls import (
    path,
    include,
)
from rest_framework.routers import DefaultRouter
from posting import views


router = DefaultRouter()
router.register('postings', views.PostingViewSet)
router.register('tags', views.TagViewSet)

app_name = 'posting'

urlpatterns = [
    path('', include(router.urls)),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CatViewSet, MissionViewSet, TargetViewSet, run_system_tests_view

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'cats', CatViewSet, basename='cat')
router.register(r'missions', MissionViewSet, basename='mission')
router.register(r'targets', TargetViewSet, basename='target')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
    path('run-pytest/', run_system_tests_view, name='run-pytest'),
]
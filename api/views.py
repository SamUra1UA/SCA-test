import requests
from rest_framework import viewsets, status, decorators
from rest_framework.response import Response
from .models import Cat, Mission, Target
from .serializers import CatSerializer, MissionSerializer, TargetSerializer


class CatViewSet(viewsets.ModelViewSet):
    queryset = Cat.objects.all()
    serializer_class = CatSerializer

    def partial_update(self, request, *args, **kwargs):
        # Specific requirement: Ability to update salary
        if 'salary' in request.data and len(request.data) > 1:
            return Response({"error": "Only salary can be updated via this endpoint."},
                            status=status.HTTP_400_BAD_REQUEST)
        return super().partial_update(request, *args, **kwargs)


class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.cat is not None:
            return Response({"error": "Mission is already assigned to a cat and cannot be deleted."},
                            status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    @decorators.action(detail=True, methods=['patch'])
    def assign_cat(self, request, pk=None):
        mission = self.get_object()
        cat_id = request.data.get('cat_id')

        try:
            cat = Cat.objects.get(pk=cat_id)
            # Check if cat already has a mission
            if hasattr(cat, 'active_mission'):
                return Response({"error": "This cat is already on another mission."},
                                status=status.HTTP_400_BAD_REQUEST)

            mission.cat = cat
            mission.save()
            return Response({"status": f"Cat {cat.name} assigned to mission."})
        except Cat.DoesNotExist:
            return Response({"error": "Cat not found."}, status=status.HTTP_404_NOT_FOUND)


class TargetViewSet(viewsets.GenericViewSet, viewsets.mixins.UpdateModelMixin):
    queryset = Target.objects.all()
    serializer_class = TargetSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Requirement: Notes/Target frozen if target or mission is complete
        if instance.is_completed or instance.mission.is_completed:
            if 'notes' in request.data or 'is_completed' in request.data:
                # We allow marking as complete IF it wasn't already complete
                if instance.is_completed and 'notes' in request.data:
                    return Response({"error": "Target is complete. Notes are frozen."},
                                    status=status.HTTP_400_BAD_REQUEST)

        return super().update(request, *args, **kwargs)
import pytest
import requests
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.safestring import mark_safe
from rest_framework import viewsets, status, decorators
from rest_framework.response import Response

from .models import Cat, Mission, Target
from .serializers import CatSerializer, MissionSerializer, TargetSerializer


# --- REST API ViewSets ---

class CatViewSet(viewsets.ModelViewSet):
    queryset = Cat.objects.all()
    serializer_class = CatSerializer

    def partial_update(self, request, *args, **kwargs):
        # Specific requirement: Ability to update salary.
        # Check if they are trying to update more than just salary.
        if 'salary' in request.data and len(request.data) > 1:
            return Response({"error": "Only salary can be updated via this endpoint."},
                            status=status.HTTP_400_BAD_REQUEST)
        return super().partial_update(request, *args, **kwargs)


class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Requirement: A mission cannot be deleted if it is already assigned to a cat
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
            # Requirement: One cat can only have one mission at a time
            if hasattr(cat, 'active_mission') and cat.active_mission:
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

        # Requirement: Notes cannot be updated if either the target or the mission is completed
        if instance.is_completed or instance.mission.is_completed:
            if 'notes' in request.data:
                return Response({"error": "Target or Mission is complete. Notes are frozen."},
                                status=status.HTTP_400_BAD_REQUEST)

        return super().update(request, *args, **kwargs)


# --- Custom Admin Test Runner ---

@staff_member_required
def run_system_tests_view(request):
    """
    Executes the pytest suite programmatically and captures results for the Admin UI.
    Protected by staff_member_required to ensure only authorized users can trigger it.
    """

    class PytestDetailedPlugin:
        def __init__(self):
            self.results = []
            self.passed_count = 0
            self.failed_count = 0

        def pytest_runtest_logreport(self, report):
            if report.when == 'call':
                # Format test names for the UI
                test_name = report.nodeid.split("::")[-1].replace("test_", "").replace("_", " ").title()
                outcome = report.outcome

                # Using Django CSS Variables for adaptive theme support
                success_color = "var(--message-success-color, #264b37)"
                error_color = "var(--message-error-color, #ba2121)"

                icon = "✔" if outcome == "passed" else "✘"
                color = success_color if outcome == "passed" else error_color

                # Transparent background colors that work on both light and dark modes
                bg_color = "rgba(40, 167, 69, 0.08)" if outcome == "passed" else "rgba(220, 53, 69, 0.08)"

                if outcome == "passed":
                    self.passed_count += 1
                else:
                    self.failed_count += 1

                self.results.append(
                    f"<div style='display: flex; align-items: center; justify-content: space-between; "
                    f"padding: 8px 12px; margin-bottom: 5px; border-radius: 6px; background: {bg_color}; "
                    f"border-left: 5px solid {color}; box-shadow: 0 1px 2px rgba(0,0,0,0.02);'>"
                    f"<span style='font-weight: 500; color: var(--body-fg, #333); font-size: 0.95em;'>{test_name}</span>"
                    f"<span style='color: {color}; font-weight: 700; font-family: monospace; font-size: 0.9em; "
                    f"text-transform: uppercase;'>{icon} {outcome}</span>"
                    f"</div>"
                )

    plugin = PytestDetailedPlugin()
    pytest.main(["api/tests.py", "--no-migrations", "-q"], plugins=[plugin])

    result_items = "".join(plugin.results)
    total = plugin.passed_count + plugin.failed_count
    pass_percent = (plugin.passed_count / total * 100) if total > 0 else 0

    summary = (
        f"<div style='margin-top: 15px; font-family: var(--font-family-primary, system-ui, sans-serif);'>"
        f"  <div style='display: flex; flex-direction: column; gap: 2px;'>"
        f"    {result_items}"
        f"  </div>"
        f"  <div style='margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border-color, #ddd);'>"
        f"    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>"
        f"       <span style='font-weight: 600; color: var(--body-fg); opacity: 0.9;'>Verification Progress</span>"
        f"       <span style='font-weight: 700; color: var(--body-fg);'>{plugin.passed_count} / {total} Passed</span>"
        f"    </div>"
        f"    <div style='width: 100%; height: 10px; background: var(--selected-bg, #f0f0f0); border-radius: 5px; overflow: hidden;'>"
        f"       <div style='width: {pass_percent}%; height: 100%; background: var(--message-success-color, #28a745); transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);'></div>"
        f"    </div>"
        f"  </div>"
        f"</div>"
    )

    if plugin.failed_count == 0:
        messages.success(request,
                         mark_safe(f"<b style='font-size: 1.1em;'>🚀 All Agency Protocols Verified!</b>{summary}"))
    else:
        messages.error(request, mark_safe(f"<b style='font-size: 1.1em;'>⚠️ Security Protocols Breached!</b>{summary}"))

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/admin/'))
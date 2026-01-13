from django.contrib import admin
from .models import Cat, Mission, Target

class TargetInline(admin.TabularInline):
    """Allows targets to be managed directly inside the Mission view."""
    model = Target
    extra = 1
    max_num = 3
    fields = ('name', 'country', 'notes', 'is_completed')

@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    """Admin interface for Missions, allowing cat assignment and target management."""
    list_display = ('id', 'cat', 'is_completed', 'target_count')
    list_filter = ('is_completed',)
    inlines = [TargetInline]

    def target_count(self, obj):
        return obj.targets.count()
    target_count.short_description = 'Targets'

@admin.register(Cat)
class CatAdmin(admin.ModelAdmin):
    """Admin interface for Spy Cats."""
    list_display = ('name', 'breed', 'years_of_experience', 'salary')
    list_filter = ('breed',)
    search_fields = ('name',)
    ordering = ('id',)

@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    """Allows individual targets to be managed and viewed independently of missions."""
    list_display = ('name', 'mission', 'country', 'is_completed')
    list_filter = ('is_completed', 'country')
    search_fields = ('name', 'mission__id')
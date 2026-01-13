from django.contrib import admin
from .models import Cat, Mission, Target


class TargetInline(admin.TabularInline):
    model = Target
    extra = 1
    max_num = 3


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'cat', 'is_completed', 'target_count')
    inlines = [TargetInline]

    def target_count(self, obj):
        return obj.targets.count()


@admin.register(Cat)
class CatAdmin(admin.ModelAdmin):
    list_display = ('name', 'breed', 'years_of_experience', 'salary')
    list_filter = ('breed',)
    search_fields = ('name',)
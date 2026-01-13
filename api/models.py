from django.db import models
from django.core.exceptions import ValidationError

class Cat(models.Model):
    name = models.CharField(max_length=100)
    years_of_experience = models.PositiveIntegerField()
    breed = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class Mission(models.Model):
    cat = models.OneToOneField(Cat, on_delete=models.SET_NULL, null=True, blank=True, related_name='active_mission')
    is_completed = models.BooleanField(default=False)

    def check_and_complete(self):
        """Requirement: After completing all targets, mission is marked completed."""
        if not self.targets.filter(is_completed=False).exists():
            self.is_completed = True
            self.save()

    def __str__(self):
        return f"Mission {self.id} - {'Complete' if self.is_completed else 'Active'}"

class Target(models.Model):
    mission = models.ForeignKey(Mission, related_name='targets', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Check if this completion finishes the mission
        if self.is_completed:
            self.mission.check_and_complete()

    class Meta:
        unique_together = ('mission', 'name')
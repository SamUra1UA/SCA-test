import requests
from rest_framework import serializers
from .models import Cat, Mission, Target


class CatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cat
        fields = '__all__'

    def validate_breed(self, value):
        """Validate breed against TheCatAPI."""
        try:
            response = requests.get("https://api.thecatapi.com/v1/breeds", timeout=5)
            if response.status_code == 200:
                valid_breeds = [breed['name'] for breed in response.json()]
                if value not in valid_breeds:
                    raise serializers.ValidationError(f"'{value}' is not a valid cat breed.")
            return value
        except requests.RequestException:
            return value

    def update(self, instance, validated_data):
        """Requirement: Only update salary via partial update."""
        if getattr(self.context.get('view'), 'action', None) == 'partial_update':
            allowed_fields = {'salary'}
            provided_fields = set(validated_data.keys())
            if not provided_fields.issubset(allowed_fields):
                raise serializers.ValidationError("Only the 'salary' field can be updated.")
        return super().update(instance, validated_data)


class TargetSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)  # Allow ID for updates

    class Meta:
        model = Target
        fields = ['id', 'name', 'country', 'notes', 'is_completed']

    def validate(self, data):
        """Requirement: Notes frozen if target or mission completed."""
        if self.instance:
            if self.instance.is_completed or self.instance.mission.is_completed:
                if 'notes' in data and data['notes'] != self.instance.notes:
                    raise serializers.ValidationError("Notes are frozen because target/mission is complete.")
        return data


class MissionSerializer(serializers.ModelSerializer):
    targets = TargetSerializer(many=True)

    class Meta:
        model = Mission
        fields = ['id', 'cat', 'is_completed', 'targets']
        read_only_fields = ['is_completed']

    def validate_cat(self, value):
        """Requirement: One cat can only have one mission at a time."""
        if value and Mission.objects.filter(cat=value).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError("This cat is already assigned to another mission.")
        return value

    def create(self, validated_data):
        targets_data = validated_data.pop('targets')
        if not (1 <= len(targets_data) <= 3):
            raise serializers.ValidationError("A mission must have 1-3 targets.")

        mission = Mission.objects.create(**validated_data)
        for target_data in targets_data:
            Target.objects.create(mission=mission, **target_data)
        return mission

    def update(self, instance, validated_data):
        """Requirement: Ability to update mission targets."""
        targets_data = validated_data.pop('targets', None)

        # Update mission fields (like assigning a cat)
        instance = super().update(instance, validated_data)

        if targets_data is not None:
            # Check 1-3 targets requirement
            if not (1 <= len(targets_data) <= 3):
                raise serializers.ValidationError("A mission must have 1-3 targets.")

            # Logic to update existing targets or create new ones
            keep_targets = []
            for target_data in targets_data:
                target_id = target_data.get('id')
                if target_id:
                    t = Target.objects.get(id=target_id, mission=instance)
                    for attr, value in target_data.items():
                        setattr(t, attr, value)
                    t.save()
                    keep_targets.append(t.id)
                else:
                    t = Target.objects.create(mission=instance, **target_data)
                    keep_targets.append(t.id)

            # Remove targets not in the update request
            instance.targets.exclude(id__in=keep_targets).delete()

        return instance
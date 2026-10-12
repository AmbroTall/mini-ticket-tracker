from rest_framework import serializers

from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    """Create/read representation."""

    class Meta:
        model = Ticket
        fields = ["id", "title", "description", "status", "priority", "created_at"]
        read_only_fields = ["id", "created_at"]


class TicketUpdateSerializer(serializers.ModelSerializer):
    """PATCH accepts status and/or priority only; anything else is rejected, not ignored."""

    class Meta:
        model = Ticket
        fields = ["status", "priority"]

    def validate(self, attrs):
        unexpected = set(self.initial_data) - set(self.fields)
        if unexpected:
            raise serializers.ValidationError(
                {name: "This field cannot be updated." for name in sorted(unexpected)}
            )
        if not attrs:
            raise serializers.ValidationError("Provide status and/or priority.")
        return attrs

from rest_framework import serializers
from users.models import User
from users.serializers import UserSerializer
from .models import Ticket

VALID_TRANSITIONS = {
    'OPEN': ['IN_PROGRESS'],
    'IN_PROGRESS': ['RESOLVED'],
    'RESOLVED': ['CLOSED'],
    'CLOSED': [],
}


class TicketSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        source='assigned_to',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Ticket
        fields = (
            'id', 'title', 'description', 'status', 'priority', 'category',
            'created_by', 'assigned_to', 'assigned_to_id',
            'created_at', 'updated_at', 'closed_at',
        )
        read_only_fields = ('id', 'created_by', 'created_at', 'updated_at', 'closed_at')

    def validate_assigned_to_id(self, value):
        request = self.context.get('request')
        if value and request.user.role != 'ADMIN':
            raise serializers.ValidationError(
                "Solo un administrador puede asignar tickets a otros usuarios."
            )
        return value

    def validate_status(self, value):
        if not self.instance:
            return value
        current_status = self.instance.status
        allowed = VALID_TRANSITIONS.get(current_status, [])
        if value != current_status and value not in allowed:
            raise serializers.ValidationError(
                f"Transición inválida: {current_status} → {value}. "
                f"Permitidas: {allowed if allowed else 'ninguna (ticket cerrado)'}."
            )
        return value

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
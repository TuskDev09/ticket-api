from rest_framework import serializers

from users.serializers import UserSerializer
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'ticket', 'user', 'content', 'created_at')
        read_only_fields = ('id', 'user', 'ticket', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['ticket_id'] = self.context['ticket_id']
        return super().create(validated_data)

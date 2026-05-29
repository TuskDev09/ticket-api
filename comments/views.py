from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound

from tickets.models import Ticket
from .models import Comment
from .serializers import CommentSerializer


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_ticket(self):
        ticket_id = self.kwargs['ticket_id']
        try:
            return Ticket.objects.get(pk=ticket_id)
        except Ticket.DoesNotExist:
            raise NotFound('Ticket not found.')

    def get_queryset(self):
        return Comment.objects.filter(
            ticket_id=self.kwargs['ticket_id']
        ).select_related('user')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['ticket_id'] = self.kwargs['ticket_id']
        return context

    def perform_create(self, serializer):
        self.get_ticket()
        serializer.save(user=self.request.user, ticket_id=self.kwargs['ticket_id'])
